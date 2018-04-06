from celery import shared_task, current_task
from import_excel.funcs import get_field_from_verbose
from django.apps import apps
from import_excel.models import TaskDuplicates


def bulk_create_excel_list(excel_list, model):
    bulk_instances = []
    current_row = 1

    for row in excel_list:
        create_dict = {}
        for k, v in row.items():
            create_dict[k] = v
        pk = model.objects.all().order_by("-id")[0].pk
        print(create_dict)
        create_dict["id"] = pk+current_row
        bulk_instances.append(model(**create_dict))
        current_row += 1
    model.objects.bulk_create(bulk_instances)
    print("FINISH EXECUTION")


@shared_task
def table_data_to_model_task(excel_list, app_label_and_model_name, unique_together):
    model = apps.get_model(app_label_and_model_name[0], app_label_and_model_name[1])
    duplicates = check_duplicates_in_model(excel_list, model, unique_together, current_task.request.id)
    if duplicates:
        from erpghost import app
        app.control.revoke(current_task.request.id, terminate=True)
        return
    print("OKAY ANGEKOMMEN !!!!")
    bulk_create_excel_list(excel_list, model)


def check_duplicates_in_model(excel_list, model, unique_together, task_id):
    duplicates = []
    excel_index = 2
    for row in excel_list:
        if "block" in row["lagerplatz"].lower():
            continue
        dict_ = {}
        for unique_field in unique_together:
            dict_[unique_field] = row[unique_field]
        duplicate = model.objects.filter(**dict_)
        if duplicate.exists():
            query_string = ""
            for unique_field in unique_together:
                val = getattr(duplicate.first(), get_field_from_verbose(unique_field, model))
                query_string += f"{unique_field}={val}&"
            query_string += f"Excel Index={excel_index}&"
            query_string = query_string[:-1]
            print(query_string)
            TaskDuplicates.objects.create(task_id=task_id, query_string=query_string)
            duplicates.append(duplicate)
        # print(f"{row} - {unique_together} - {duplicate}")
        excel_index += 1
    if len(duplicates) > 1:
        return duplicates
