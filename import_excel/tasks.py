from celery import shared_task
from import_excel.funcs import bulk_create_excel_list
from django.apps import apps


@shared_task
def table_data_to_model_task(excel_list, app_label_and_model_name, related_models, verbose_fields,
                             main_model_related_names):
    model = apps.get_model(app_label_and_model_name[0], app_label_and_model_name[1])
    bulk_create_excel_list(excel_list, model, related_models, verbose_fields, main_model_related_names)
