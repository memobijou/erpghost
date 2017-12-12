var generate_master_detail = function(){

	var master_div = document.createElement("div");
    var detail_div = document.createElement("div");

    var row = document.createElement("div");
    row.className = "row";

    master_div.className = "col-md-2";
    detail_div.className = "col-md-9 col-md-offset-1";

    master_div.style = "background-color:white;height:400px;";
    detail_div.style = "background-color:white;height:400px;";

    row.appendChild(master_div);
    row.appendChild(detail_div);

    return {"master": master_div, "detail": detail_div, "row": row};
}


var generate_table = function(){
	var table = document.createElement("table");
	var thead = document.createElement("thead");
	var tbody = document.createElement("tbody");
	table.appendChild(thead);
	table.appendChild(tbody);
    return {"table": table, "tbody": tbody, "thead": thead};
}
