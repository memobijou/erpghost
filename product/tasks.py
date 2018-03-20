from celery import shared_task
from django.apps import apps


@shared_task
def table_data_to_model_task(records_list, main_model, related_models):
    bulk_instances = []
    model = apps.get_model(main_model[0], main_model[1])
    for record in records_list:
        create_dict = {}
        for k, v in record.items():
            model_field_attr = get_field_from_verbose(k, model)
            create_dict[model_field_attr] = v
            related_instance = create_related_instance_from_verbose(k, model, related_models, v)
            if related_instance:
                create_dict[model_field_attr] = related_instance
        ## DEBUG ##

        for a,b in create_dict.items():
            print(f"{a} - {b} - {len(str(b))}")

        ###########
        bulk_instances.append(model(**create_dict))
    model.objects.bulk_create(bulk_instances)
    print(apps.get_model("product", "Manufacturer"))


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
                        field_attr = field.attname.replace("_id", "")

                        related_model = apps.get_model(related_models[field_attr]["app_label"],
                                                       related_models[field_attr]["model_name"])
                        related_verbose_name = related_models[field_attr]["verbose_name"]
                        related_attr = get_field_from_verbose(related_verbose_name, related_model)

                        new_instance = related_model.objects.create(**{related_attr: value})
                        return new_instance
#        related_models = {"manufacturer": RelatedModel(app_label="product", model_name="Manufacturer",
#                                            verbose_name="Herstellernummer")}
