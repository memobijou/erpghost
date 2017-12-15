// requirejs(["app/main"]);


requirejs.config({
    "paths": {
      "jquery": "../vendor/jquery",
      "bootstrap": "../vendor/bootstrap.min",
      // "masterdetail": "../app/masterdetail",
      // "functions": "../app/functions",
    },
    "shim": {
        "bootstrap": ["jquery"],
        "masterdetail": ["bootstrap" ,"functions"],
        "tables": ["bootstrap" ,"functions"],

    }
});


// define(["functions", "bootstrap"],function(functions) {
//   return {
//     test_func: function() {
//       // $ = jQuery  
//       jQuery(document).ready(function(){
//         alert("Ich bin jQuery");

//       });
//       alert("Asooo so geht das!");
//     }
//   }
// });



define([
    // "../vendor/jquery",
    // "../vendor/bootstrap.min",
    "jquery",
    // "functions",
    // "masterdetail",
    // "tables",
    "bootstrap",

], function($, functions)
{
    $(function()
    {

        //do stuff
        // test_func();



    });
});










