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
        var th = document.createElement("th");
        th.innerHTML = fields[f]; 
        tr.appendChild(th);

    }

    thead.appendChild(tr);
    return thead
}



var fill_master_detail = function(query, detail_div, exclude){
    var master_value = query.str;
    var detail = query;

    for(var k in Object.keys(detail)){
         var column = Object.keys(detail)[k];
         if(is_in_array(column, exclude)){
          continue;
        }
         var col_b = document.createElement("b");
         col_b.innerHTML = column + ": ";
         detail_div.appendChild(col_b);
         var val_span = document.createElement("span");
         val_span.innerHTML = detail[column];
         detail_div.appendChild(val_span);
         detail_div.appendChild(document.createElement("br"));
    }

}



var queryset_to_master = function(response, master_tbody){
var master_rows = [];
for(var r in response){
    var query = response[r];
    var master_value = query.str;

    var tr = document.createElement("tr");
    tr.style.cursor = "pointer";

    var td = document.createElement("td");
    var b = document.createElement("b");
    b.innerHTML = master_value;
    
    td.appendChild(b);
    tr.appendChild(td);
    master_tbody.appendChild(tr); 

    var detail_values = query[master_value];
   
    master_rows.push({"row": tr, "query": query });



    // }
    // alert(master_value + " : " + JSON.stringify(product_detail));

}

return master_rows

}




function show_query_on_detail_click(row, detail_view, query, exclude){

        row.onclick = function(){
            highlight_table_row(row);
            remove_all_childs_of_element(detail_view);
            fill_master_detail(query, detail_view, exclude);

        }


}

 

// DAMIT DIESE FUNKTION FUNKTIONIERT MÜSSEN queryset UND field_names IN JAVASCRIPT DEFINIERT SEIN
function MasterDetailToListView(response, exclude=[]){


    var field_names = get_field_names_from_json(response);


    var master_detail = generate_master_detail();
    var master = master_detail.master;
    var detail = master_detail.detail;
    detail.style.padding = "25px";

    var main_container = document.getElementById("main-container");
    main_container.appendChild(master_detail.row);

    var table_components = generate_table();

    var table = table_components.table;
    var tbody = table_components.tbody;
    var thead = table_components.thead; 

    thead = create_header_from_array(field_names, thead, ["id", "str"]);

    table.style.position = "absolute";
    table.style.width = "100%";
    table.style.left = 0;
    table.style.backgroundColor = "white";
    table.className = "table table-bordered table-hover";

    master.appendChild(table);


    var master_rows = queryset_to_master(response, tbody);
    for(var m in master_rows){

        var master_row_components = master_rows[m];
        var master_row = master_row_components.row;
        var query = master_row_components.query;
        show_query_on_detail_click(master_row, detail, query, exclude)

        if(m == 0){
            fill_master_detail(query, detail, exclude);
            highlight_table_row(master_row);

        }

    }

    return {"master": master, "detail": detail, "master_tbody": tbody, "master_thead": thead, "master_rows": master_rows}
}





