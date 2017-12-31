var app = angular.module('ng_scanorder', []);
app.controller('main_ctrl', function($scope, $http){

	$scope.product_match = {"input": "", "match": "INIT"}

	$scope.confirm_product = {"product": $scope.product_match.input, "amount": ""}

	$scope.product_orders = null;


	var find_matching_product_order = function(to_find_value, criteria){
		for(var i = 0; i< $scope.product_orders.length; i++){
			var row = $scope.product_orders[i];
			var product = row.product;
			var confirmed = row.confirmed;
			if(confirmed == null && product[criteria] == to_find_value){
				return row
			}
		}
		return null
	};

	$scope.checkProduct = function(){

		url = "http://127.0.0.1:8000/product/api/"
		querystring = "?ean=" + $scope.product_match.input
		if($scope.product_match.input.length == 13){

			var product_order = find_matching_product_order($scope.product_match.input, "ean");
			if(product_order){
				$scope.product_match.match = true;
				// alert(JSON.stringify(product_order));
				$scope.confirm_product  = {"ean": product_order.product.ean, "amount": product_order.amount}

			}else{
				$scope.product_match.match = false;
			}
		}else{
				$scope.product_match.match = null;
		}
	};


	$scope.init_function = function(json_){
		$scope.product_orders = json_;
	};

});
