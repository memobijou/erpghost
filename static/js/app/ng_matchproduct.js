var app = angular.module('ng_matchproduct', []);
app.controller('match_ctrl', function($scope, $http){
		$scope.class = "";
		$scope.match_product = function(e, value, hidden_model){
			// alert(value + JSON.stringify(Object.keys(this)) );
			// alert(this.parent);

			var errorFunc = function(input, hidden_model, value){
				$scope[hidden_model] = "";
			    input.setAttribute("class", "error_input");
			}

			var successFunc = function(input, hidden_model, value){
				$scope[hidden_model] = value;
			    input.setAttribute("class", "success_input");
			} 

			var el = e.target;
			if(value.length == 13){
			    $http.get("/api/product_match/" + value)
				    .then(function(response) {
				        // $scope.myWelcome = response.data;
				        if(response.data.match){
        					successFunc(e.target, hidden_model, response.data.id);
				        }else{
        					errorFunc(e.target, hidden_model, value);

				        }
			    });
				return true;

			}else if(value.length == 0){
				e.target.setAttribute("class", "");
			}
			else{
				errorFunc(e.target, hidden_model, value);
				return false;
			}

		}

				}
);