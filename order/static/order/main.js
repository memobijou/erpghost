require(["tables"],function(){
	jQuery(document).ready(function(){
				get_("/order/api", TableToListView, [["id", "str"]]);


});

    // MasterDetailToListView(queryset, fields_name);
});