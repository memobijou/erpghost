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


var queryset_to_master = function(queryset, master_tbody){
var master_rows = [];
    
for(var p in queryset){
    var query = queryset[p];
    var master_value = Object.keys(query)[0];

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


function show_query_on_detail(row, detail_view, query){
        row.onclick = function(){
            remove_all_childs_of_element(detail_view);
            fill_master_detail(query, detail_view);

        }
}



// DAMIT DIESE FUNKTION FUNKTIONIERT MÜSSEN queryset UND field_names IN JAVASCRIPT DEFINIERT SEIN
function MasterDetailToListView(){

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

    thead = create_header_from_array(field_names, thead, ["id"]);

    table.style.position = "absolute";
    table.style.width = "100%";
    table.style.left = 0;
    table.style.backgroundColor = "white";
    table.className = "table table-bordered";

    master.appendChild(table);


    var master_rows = queryset_to_master(queryset, tbody);

    for(var m in master_rows){
        var master_row_components = master_rows[m];
        var master_row = master_row_components.row;
        var query = master_row_components.query;

        show_query_on_detail(master_row, detail, query)
    }

    return {"master": master, "detail": detail, "master_tbody": tbody, "master_thead": thead, "master_rows": master_rows}
}




function TableToListView(exclude=[]){

        var table_components = generate_table();
        var table = table_components.table;
        table.style.backgroundColor = "white";

        var tbody = table_components.tbody;
        var thead = table_components.thead;
        thead = create_header_from_array(field_names, thead, exclude);
        table.className = "table table-bordered";


        fill_ordinary_table(queryset, tbody, exclude);

        var main_container = document.getElementById("main-container");
        main_container.appendChild(table);

        return {"table": table, "tbody": tbody, "thead": thead};

}   



var remove_all_childs_of_element = function(element){
    while(element.firstChild){
        element.removeChild(element.firstChild);
    }
}