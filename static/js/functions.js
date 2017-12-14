var generate_master_detail = function(){

	var master_div = document.createElement("div");
    var detail_div = document.createElement("div");

    var row = document.createElement("div");
    row.className = "row";

    master_div.className = "col-md-2";
    detail_div.className = "col-md-9 col-md-offset-1 table-bordered";

    // master_div.style = "background-color:white;height:400px;";
    // detail_div.style = "background-color:white;height:400px;";
    detail_div.style.backgroundColor = "white";
    master_div.style.height = "400px";
    detail_div.style.height = "400px";

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


var parse_json = function(toparse_string){
    toparse_string = toparse_string.replace(/\'/g, '"');
    return JSON.parse(toparse_string)
}


var create_header_from_array = function(fields, thead, exclude){
    var tr = document.createElement("tr");

    for(var f in fields){
        if(exclude && exclude.includes(fields[f])) continue;
        var td = document.createElement("td");
        td.innerHTML = fields[f]; 
        tr.appendChild(td);

    }

    thead.appendChild(tr);
    return thead
}



var fill_master_detail = function(query, detail_div){
    var master_value = Object.keys(query)[0];
    var detail = query[master_value];

    for(var k in Object.keys(detail)){
         var column = Object.keys(detail)[k];
         var col_b = document.createElement("b");
         col_b.innerHTML = column + ": ";
         detail_div.appendChild(col_b);
         var val_span = document.createElement("span");
         val_span.innerHTML = detail[column];
         detail_div.appendChild(val_span);
         detail_div.appendChild(document.createElement("br"));
    }

}



var fill_ordinary_table = function(queryset, tbody, exclude){


    for(var q in queryset){

        var master_value = Object.keys(queryset[q])[0];
        var detail_values = queryset[q][master_value];

        var tr = document.createElement("tr");
        for(var d in detail_values){
            var column = d;
            if(exclude.includes(column)){ 
                continue;
            }

            var value = detail_values[d];
            var td = document.createElement("td");
            td.innerHTML = value;
            tr.appendChild(td);
            tbody.appendChild(tr);
        }

}



}


var remove_all_childs_of_element = function(element){
    while(element.firstChild){
        element.removeChild(element.firstChild);
    }
}