QUnit.test( "hello test", function( assert ) {
  assert.ok( 1 == "1", "Passed!" );


  var obj = {},
    hasOwn = Object.prototype.hasOwnProperty;

  assert.ok (obj.toString !== undefined);
  assert.ok (obj.constructor.prototype.toString !==undefined);
  assert.ok (obj.toString === obj.constructor.prototype.toString);
  assert.ok(hasOwn.call(obj,'toString') === false,"toString is not in obj");
  assert.ok(hasOwn.call(obj.constructor.prototype,'toString') === true,"toString is belong to Object.prototype");

});



QUnit.test( "test ajax api", function( assert ) {

  var done = assert.async();
  var xhr = jQuery.ajax({url: 'api/current_run', type:'GET'})
  .always(function(data,status){
    console.log(data);
    $.each(data,function(k,v){
      console.log(k);
      console.log(v);

    });
    assert.equal(status,"success");
    done();
  });


});


function _extend(obj) {
  [].slice.call(arguments, 1).forEach(function (source) {
    if (source) {
      for (var prop in source) {
        obj[prop] = source[prop];
      }
    }
  });
  return obj;
}

QUnit.test("on and trigger",function(assert){


  var obj = {count:0};

  _extend(obj,Gillie.Events);

  obj.on('event',function(){this.count +=1 ;},obj);

  obj.trigger('event');

  assert.ok(obj.count == 1,"count should equal 1 and  actual: " + obj.count);
  obj.trigger('event');
  assert.ok(obj.count == 2,"count should equal 2 and  actual: " + obj.count);


});


QUnit.test( 'Initialize', function(assert) {

  var Handler = Gillie.Handler.extend({

    initialize: function() {
      this.name = 'John';
    }
  });

  assert.strictEqual( new Handler().name, 'John' );

});

QUnit.test( 'delegateEvents and calling class methods', 3, function(assert) {

  var count = 0;
  // Dummy element
  var dummyEl = $( '<a class="dummy" href="#"></a>' );
  dummyEl.appendTo( "body" );

  var Handler = Gillie.Handler.extend({

    initialize: function() {},

    el: 'body',

    events: {
      'click .dummy': 'increment'
    },

    increment: function() {
      this.incrementCallback();
    },

    incrementCallback: function() {
      count++;
    },

  });

  var handler = new Handler();

  // Trigger clicks
  dummyEl.trigger( 'click' );
  assert.equal( count, 1 );

  dummyEl.trigger( 'click' );
  assert.equal( count, 2 );

  dummyEl.trigger( 'click' );
  assert.equal( count, 3 );

});
