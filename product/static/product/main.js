$(document).ready(function(e){

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

for(var p in queryset){
    var query = queryset[p];
    var master_value = Object.keys(query)[0];

    var tr = document.createElement("tr");
    var td = document.createElement("td");
    var b = document.createElement("b");
    b.innerHTML = master_value;
    
    td.appendChild(b);
    tr.appendChild(td);
    tbody.appendChild(tr); 

    var detail_values = query[master_value];
   

    (function(tr, query, detail){
        tr.style.cursor = "pointer";
        tr.onclick = function(){
            remove_all_childs_of_element(detail);
            fill_master_detail(query, detail);

        }

    })(tr, query, detail);



    // }
    // alert(master_value + " : " + JSON.stringify(product_detail));

}


});

