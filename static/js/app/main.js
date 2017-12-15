requirejs.config({
    "paths": {
      "jquery": "../vendor/jquery",
      "bootstrap": "../vendor/bootstrap.min",
      // "masterdetail": "../app/masterdetail",
      // "functions": "../app/functions",
    },
    "shim": {
        "jquery": {
            exports: "$", 

        },
        "bootstrap": ["jquery"],
        "masterdetail": ["bootstrap" ,"functions"],
        "tables": ["bootstrap" ,"functions"],


    }
});





define([
    // "../vendor/jquery",
    // "../vendor/bootstrap.min",
    // "jquery",
    // "functions",
    // "masterdetail",
    // "tables",
    // "bootstrap",

], function()
{
 
});










