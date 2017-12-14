$(document).ready(function(e){

// alert(field_names);
// alert(field_names);


var table_components = generate_table();
var table = table_components.table;
table.style.backgroundColor = "white";

var tbody = table_components.tbody;
var thead = table_components.thead;
var exclude = ["id"];
thead = create_header_from_array(field_names, thead, exclude);
table.className = "table table-bordered";


fill_ordinary_table(queryset, tbody, exclude);

var main_container = document.getElementById("main-container");
main_container.appendChild(table);


});