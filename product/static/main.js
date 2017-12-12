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

table.style = "position: absolute;width: 100%;left: 0;";
table.className = "table table-bordered";

var head_row = document.createElement("tr");
var head_td = document.createElement("td");
head_td.innerHTML = "EAN";	
head_row.appendChild(head_td);
thead.appendChild(head_row);
table.appendChild(thead);
master.appendChild(table);

for(var p in products){
    var product = products[p];
    var master_value = Object.keys(product)[0];

    var tr = document.createElement("tr");
    var td = document.createElement("td");
    var b = document.createElement("b");
    b.innerHTML = master_value;
    
    td.appendChild(b);
    tr.appendChild(td);
    tbody.appendChild(tr); 

    var product_detail = product[master_value];

    for(var k in Object.keys(product_detail)){
    	var column = Object.keys(product_detail)[k];
    	var col_b = document.createElement("b");
    	col_b.innerHTML = column + ": ";
    	detail.appendChild(col_b);
    	var val_span = document.createElement("span");
    	val_span.innerHTML = product_detail[column];
    	detail.appendChild(val_span);
    	detail.appendChild(document.createElement("br"));


    }

}


});

