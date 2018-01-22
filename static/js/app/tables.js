var generate_table = function () {
    var table = document.createElement("table");
    var thead = document.createElement("thead");
    var tbody = document.createElement("tbody");
    table.appendChild(thead);
    table.appendChild(tbody);
    return {"table": table, "tbody": tbody, "thead": thead};
}


var fill_table = function (queryset, tbody, exclude) {
    for (var q in queryset) {

        var master_value = queryset[q].str;
        var detail_values = queryset[q];

        var tr = document.createElement("tr");
        for (var d in detail_values) {
            var column = d;
            if (exclude.includes(column)) {
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


function TableToListView(response, exclude=[]) {

    var field_names = get_field_names_from_json(response);

    var table_components = generate_table();
    var table = table_components.table;
    table.style.backgroundColor = "white";

    var tbody = table_components.tbody;
    var thead = table_components.thead;
    thead = create_header_from_array(field_names, thead, exclude);
    table.className = "table table-bordered";


    fill_table(response, tbody, exclude);

    var main_container = document.getElementById("main-container");
    main_container.appendChild(table);

    return {"table": table, "tbody": tbody, "thead": thead};

}   