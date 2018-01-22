var app = angular.module('ng_scanorder', []);
app.controller('main_ctrl', function ($scope, $http, $timeout) {

    $scope.product_match = {"input": "", "match": "INIT"}

    $scope.confirm_product = {"product": $scope.product_match.input, "amount": ""}

    $scope.product_orders = null;


    var find_matching_product_order = function (to_find_value, criteria) {
        for (var i = 0; i < $scope.product_orders.length; i++) {
            var row = $scope.product_orders[i];
            var product = row.product;
            var confirmed = row.confirmed;
            if (confirmed == null && product[criteria] == to_find_value) {
                return row
            }
        }
        return null
    };

    $scope.checkProduct = function () {
        $scope.scan_product($scope.product_match.input);

        url = "http://127.0.0.1:8000/product/api/"
        querystring = "?ean=" + $scope.product_match.input

        if ($scope.product_match.input.length == 13) {

            var product_order = find_matching_product_order($scope.product_match.input, "ean");
            if (product_order) {
                $scope.product_match.match = true;
                // alert(JSON.stringify(product_order));
                $scope.confirm_product = {
                    "ean": product_order.product.ean,
                    "amount": product_order.amount,
                    "id": product_order.id,
                }

            } else {
                $scope.product_match.match = false;
            }
        } else {
            $scope.product_match.match = null;
        }
    };


    $scope.is_sku = false;
    $scope.len = 0;

    $scope.scan_product = function (input) {

        var value = input;
        $scope.len = input.length;

        if ($scope.len > 13) {
            lastchar = value[$scope.len - 1];
            value = lastchar;
            $scope.product_match.input = lastchar;
        }

        if ($scope.is_sku == true) {
            lastchar = value[$scope.len - 1];
            value = lastchar;
            $scope.product_match.input = lastchar;
            $scope.is_sku = false;
        }

        if ($scope.len == 8) {
            $scope.is_sku = watchInputLength($scope.len, 8, $scope.is_sku).then(function (data) {
                $scope.is_sku = data.is_sku;
            });
        }


        function watchInputLength(value, against, bool) {

            return $timeout(function () {
                if (value == against) {
                    if ($scope.len == against) {
                        bool = true;
                    } else {
                        bool = false;
                    }
                } else {
                    bool = false;
                }

                return {
                    is_sku: bool
                };

            }, 500);


            //  setTimeout(function () {
            //    if(value == against){
            // is_sku = true;
            //      	return true;
            //  	} 
            //  }, 200);
        }

    }


    $scope.init_function = function (json_) {
        $scope.product_orders = json_;
    };

});
