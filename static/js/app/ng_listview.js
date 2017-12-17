var app = angular.module('ng_listview', []);
app.controller('masterdetail_ctrl', function($scope){
	$scope.clickFunction = function(id,querylist){
		// alert(id  + " : " + JSON.stringify(querylist));
		for(var query in querylist) if(querylist[query].id == id){ var match_result = querylist[query]; break;}
			$scope.detail_query = match_result;
		}

	}
);

// app.controller('filter_ctrl', ['$scope', '$http', function($scope, $http){
	
// 	var initializing = true;
// 	$scope.changeFunction = function(e){
// 				// alert("ab: " + e.target)
// 		        angular.element($event.target.form).triggerHandler('submit');
// 	};


// 	$scope.$watch("fields", function(){
// 	  if(initializing == true){
// 	    initializing = false;	
// 	  }else{
// 	  	// alert(initializing);
// 	  	$scope.formSubmit();
// 	  }
// 	}, true);

// 	$scope.formSubmit = function(){
//         var data=$scope.fields;
// 		// alert(JSON.stringify(data));
// 		// $http.get("/product/api/").then(function(response){

// 		// 	// alert(JSON.stringify(response.data));

// 		// });
// 		// document.getElementById("filter_form").submit();
// 	}
// }]);
