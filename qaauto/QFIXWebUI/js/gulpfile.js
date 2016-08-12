var gulp = require("gulp");
var gutil = require("gulp-util");
var webpack = require("webpack")
var webpackDevSvr = require("webpack-dev-server");

gulp.task("webpack",function(callback){

  webpack({
    entry: './src/test.js',
    output: {
      path: '../static/js',
      filename: 'app.bundle.js'
      }

  },function(err,stats){

    if(err) throw new gutil.PluginError("webpack",err);

      gutil.log("[webpack]",stats.toString({ 
      //output options 
    }));

    
  });

  callback();

});
