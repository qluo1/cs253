/**
 */
(function (window) {
  var root = window,
    console = root.console,
    $ = root.jQuery,
    _ = root._,
    current_test,
    tpl_tbl,
    tpl_row,
    tpl_result;

  current_test = {

      url: 'api/current_run',
      /* div */
      el: 'div #current_run',
    
    };
  //template must already loaded into html
  tpl_tbl   = _.template($("#templates #current_run_table").text());
  tpl_row   = _.template($("#templates #current_run_row").text());
  tpl_result = _.template($("#templates #current_run_result").text());

  _.extend(current_test,window.Gillie.Events);

  // self register event
  current_test.on("update",current_test.on_update);

  current_test.fetch_current_run = function(){

    var that = this;
    $.getJSON(this.url,function(data){
      console.log("getJSON " + data);
      that.trigger('update',data);
    });
    // reload every  1 second
    root.setTimeout(function(){current_test.fetch_current_run();},10000);
  };
  //
  // update event triggered and update UI
  current_test.on_update = function(data){
    
    console.log("on_update called: " + data);

    this.current_status = data;
    
    var tpl_row_str = '',
        tpl_table_str = '';
    // update UI here
    _.each(this.current_status,function(v,k){
      console.log(k);
      //console.log(v);

      var num_runner = 0,
          tpl_result_str;
      if (v.runner && v.runner.length > 1)
      {
        num_runner = v.runner.length -1;
      }
      //console.log(v.result);

      tpl_result_str = tpl_result(v.result);

      console.log(tpl_result_str);
      tpl_row_str += tpl_row({tc: k,
                              runner: num_runner,
                              result: tpl_result_str});
    });

    tpl_table_str = tpl_tbl({rows: tpl_row_str});
    console.log(tpl_table_str);
    // render  
    $(this.el).html(tpl_table_str);
  };
  // self register event
  current_test.on("update",current_test.on_update);
  // run load
  current_test.fetch_current_run();

    
})(this);
