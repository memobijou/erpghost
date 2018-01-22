var get_ = function (url, f, args=[]) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url);
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4) {
            if (xhr.status >= 200 && xhr.status <= 299) {
                args = prepend_array(JSON.parse(xhr.responseText), args);
                f.apply(this, args);
            }
        }
    }
    xhr.send();
}


var prepend_array = function (el, arr) {
    var new_arr = [];
    new_arr.push(el);
    for (var i = 0; i < arr.length; i++) {
        new_arr.push(arr[i]);
    }
    return new_arr;
}


var get_field_names_from_json = function (response) {
    var first_row = response[0];
    return Object.keys(first_row);
}

var parse_json = function (toparse_string) {
    toparse_string = toparse_string.replace(/\'/g, '"');
    return JSON.parse(toparse_string)
}


var test_func = function () {

}

var create_header_from_array = function (fields, thead, exclude) {
    var tr = document.createElement("tr");

    for (var f in fields) {
        if (exclude && exclude.includes(fields[f])) continue;
        var th = document.createElement("th");
        th.innerHTML = fields[f];
        tr.appendChild(th);

    }

    thead.appendChild(tr);
    return thead
}


var highlight_table_row = function (tr) {
    var parent = tr.parentElement;
    var trs = parent.getElementsByTagName("tr");

    for (var i = 0; i < trs.length; i++) {
        trs[i].className = trs[i].className.replace("active", "");
    }

    if (!tr.className.includes("active")) {
        tr.className = tr.className + " active";
    }

}

var is_in_array = function (x, arr) {
    for (var a in arr) {
        if (x == arr[a]) {
            return true
        }
    }
    return false;
}


var remove_all_childs_of_element = function (element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}