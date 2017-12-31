var app = angular.module('ng_matchproduct', []);
// app.config(function($interpolateProvider) {
//         $interpolateProvider.startSymbol('{$');
//         $interpolateProvider.endSymbol('$}');
//     });
app.controller('match_ctrl', function($scope, $http){
		$scope.class = "";

		$scope.tablerows = [];

		$scope.table = {};

		$scope.has_exception = false;


		$scope.store_row = function(count, id, name, choices, field_value, match_choices, field_type, error_msg){

			var table = $scope.table;

			if(count in table){
			}else{
				table[count] = [];
			}
			var dict_ = {};
			dict_["count"] = count;
			dict_["id"] = id;
			dict_["name"] = name;
			dict_["choices"] = choices;
			dict_["class"] = "";
			dict_["errors"] = error_msg;
			if(choices == ""){  // choices ist bei product_match leerer string
				dict_["is_match_field"] = true;
				dict_["hidden_value"] = ((field_value == "None") ? null : field_value);
				if(match_choices){
					dict_["visible_value"] = match_choices[field_value];
				}else{
					dict_["visible_value"] = "";					
				}
			}else{
				if(field_type){
					// alert(field_type);
					dict_["field_type"] = field_type
				}
				dict_["field_value"] = ((field_value == "None") ? null : field_value);
			}

			table[count].push(dict_);


			// alert(JSON.stringify(choices));
			// alert(JSON.stringify($scope.table));
		};

	    $scope.addRow = function (total_forms_id) {
	    	var total_forms_input = document.getElementById(total_forms_id);
	    	var table = $scope.table;
	    	var last_count = Math.max.apply(Math, Object.keys(table));

	    	var new_row = angular.copy(table[last_count]);

	    	var new_count = last_count + 1;

	    	for(var c in new_row){
	    		var col = new_row[c];
	    		col.id = col.id.replace(last_count, new_count);
	    		col.name = col.name.replace(last_count, new_count);
	    		col.visible_value = "";
	    		col.hidden_value = "";
	    		col.class = "";
	    		if(col.field_value){
	    			col.field_value = "";
	    		}
	    	}

    	    table[new_count] = new_row;
	    	total_forms_input.value = parseInt(total_forms_input.value) + parseInt(1);


    	}

	    $scope.removeChoice = function (z) {
    	    $scope.tablerows.splice(z,1);
	    };

		$scope.match_product = function(col){

			var value = col.visible_value;

			var errorFunc = function(value, col){
				col.hidden_value = "";
				col.class = "error_input";
			}

			var successFunc = function(value, col){
				col.hidden_value = value;
				col.class = "success_input";
			} 

			if(value.length == 13){
			    $http.get("/api/product_match/" + value)
				    .then(function(response) {
				        if(response.data.match){
        					successFunc(response.data.id, col);
				        }else{
        					errorFunc(value, col);

				        }
			    });
				return true;

			}else if(value.length == 0){
				col.class = "";
			}
			else{
				errorFunc(value, col);
				return false;
			}

		}

		$scope.$watch('table', function(new_val, old_val){

			for(var i in new_val){
				var has_exception = false;
				for(var j in new_val[i]){
					if(new_val[i][j].class.includes("error_input")){
						$scope.has_exception = true;
						has_exception = true;
						break;
					}
				}
				if(has_exception == true){
					break;
				}
			}

			if(has_exception == false){
				$scope.has_exception = false;
			}
		}, true);

				}
);