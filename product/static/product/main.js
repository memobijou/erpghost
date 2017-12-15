// require(["functions"],function(){
// $(document).ready(function(e){
//     MasterDetailToListView();
// });
// });


require(["masterdetail"],function(){
	$(document).ready(function(){
				get_("/product/api", MasterDetailToListView, [["id", "str"]]);


});

    // MasterDetailToListView(queryset, fields_name);
});