import pyexcel
from django.apps import apps


def get_table_header(file_type, content):
    sheet = pyexcel.get_sheet(file_type=file_type, file_content=content)
    header = sheet.row[0]
    return header


def get_records_as_list_with_dicts(file_type, content, header, excel_header_fields, replace_header_fields=None):
    records = pyexcel.get_records(file_type=file_type, file_content=content)
    records_list = []
    excel_header_fields = [field.lower() for field in excel_header_fields]
    for record in records:
        row = {}
        for header_field in header:
            if header_field.lower() in excel_header_fields:
                if replace_header_fields:
                    if header_field in replace_header_fields:
                        row[replace_header_fields[header_field]] = record[header_field]
                        continue
                row[header_field] = record[header_field]
        records_list.append(row)
    print(records_list)
    return records_list


def check_excel_header_fields_not_in_header(header, excel_header_fields):
    header = [title.lower() for title in header]
    wrong_excel_header_fields = []
    for excel_header_field in excel_header_fields:
        if excel_header_field.lower() not in header:
            wrong_excel_header_fields.append(excel_header_fields)
    if len(wrong_excel_header_fields) > 0:
        return wrong_excel_header_fields


def compare_header_with_model_fields(header, model_class, excel_header_fields, replace_header_fields=None):
    error_fields = []
    verbose_fields = []
    excel_header_fields = [excel_header_fields_field.lower() for excel_header_fields_field in excel_header_fields]

    if replace_header_fields:
        tmp_header = []
        for field in header:
            if field in replace_header_fields:
                tmp_header.append(replace_header_fields[field])
            else:
                tmp_header.append(field)
        header = tmp_header

    for field in model_class._meta.get_fields():
        if hasattr(field, "verbose_name"):
            verbose_fields.append(field.verbose_name.lower())

    for title in header:
        title = title.lower()

        if title in excel_header_fields:
            error_fields.append(get_title_error_or_success(title, verbose_fields))
        else:
            error_fields.append((title, "ignore"))

    has_error = check_error_fields_has_error(error_fields, excel_header_fields)
    all_fields_are_success = check_all_fields_are_success(error_fields, excel_header_fields)

    if has_error is True or all_fields_are_success is False:
        return error_fields


def check_error_fields_has_error(error_fields, excel_header_fields):
    for title, status in error_fields:
        title = title.lower()
        if title in excel_header_fields:
            if status == "error":
                return True
    return False


def check_all_fields_are_success(error_fields, excel_header_fields):
    for title, status in error_fields:
        title = title.lower()
        if title in excel_header_fields:
            if status == "error":
                return False
    return True


def get_title_error_or_success(title, verbose_fields):
    if title in verbose_fields:
        return title, "success"
    else:
        return title, "error"


def check_excel_for_duplicates(excel_list):
    duplicates = []
    excel_index = 2

    for row in excel_list:
        row_occurences = 0

        for next_row in excel_list:
            if next_row == row:
                row_occurences += 1
            if row_occurences == 2:
                duplicates.append((row, excel_index))
                print(duplicates)
                break
        excel_index += 1
    return duplicates


def bulk_create_excel_list(excel_list, model, related_models):
    bulk_instances = []
    current_row = 1

    for row in excel_list:
        create_dict = {}
        for k, v in row.items():
            model_field_attr = get_field_from_verbose(k, model)
            create_dict[model_field_attr] = v
            related_instance = create_related_instance_from_verbose(k, model, related_models, v)
            #print(f"{current_row}: {k} : {v}")
            if related_instance:
                create_dict[model_field_attr] = related_instance
        bulk_instances.append(model(**create_dict))
        current_row = current_row + 1
    model.objects.bulk_create(bulk_instances)
    print("FINISH EXECUTION")


def get_field_from_verbose(verbose_name, model):
    for field in model._meta.get_fields():
        if hasattr(field, "verbose_name"):
            if field.verbose_name == verbose_name:
                if field.is_relation and field.related_model:
                    return field.attname.replace("_id", "")
                return field.attname


def create_related_instance_from_verbose(verbose_name, model, related_models, value):
    for field in model._meta.get_fields():
        if field.is_relation and field.related_model:
            if hasattr(field, "verbose_name"):
                if field.verbose_name == verbose_name:
                        related_model = apps.get_model(related_models[verbose_name.lower()]["app_label"],
                                                       related_models[verbose_name.lower()]["model_name"])
                        related_verbose_name = related_models[verbose_name.lower()]["verbose_name"]
                        related_attr = get_field_from_verbose(related_verbose_name, related_model)

                        new_instance = related_model.objects.create(**{related_attr: value})
                        return new_instance
