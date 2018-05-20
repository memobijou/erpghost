from product.models import Product


def validate_product_order_or_mission_from_post(many_to_many_form_class, amount_forms, request):
    invalid_form = False

    for field in many_to_many_form_class.base_fields:
        amount_forms = len(request.POST.getlist(field))

    for i in range(0, amount_forms):
        data = {}
        for key in request.POST:
            if key in many_to_many_form_class.base_fields:
                value = request.POST.getlist(key)[i]
                data[key] = value
        if many_to_many_form_class(data=data).is_valid() is False:
            invalid_form = True
    if invalid_form is True:
        return False
    else:
        return True


def create_product_order_or_mission_forms_from_post(many_to_many_model, many_to_many_form, amount_forms,
                                                    order_or_mission_key, obj, request, start):
    for field in many_to_many_form.base_fields:
        amount_forms = len(request.POST.getlist(field))

    bulk_instances = []
    for i in range(start, amount_forms):
        print(f"i: {i} : {amount_forms}")
        data = {}
        to_delete = False
        for key in request.POST:
            if key in many_to_many_form.base_fields:
                value = request.POST.getlist(key)[i]
                if key == "ean":
                    product = Product.objects.filter(ean=value.strip()).first()
                    if product:
                        data["product"] = product
                    continue
                elif key == "delete":
                    if value == "on":
                        to_delete = True
                        break

                data[key] = value
        data[order_or_mission_key] = obj

        if to_delete is True:
            many_to_many_model.delete()
            continue
        bulk_instances.append(many_to_many_model(**data))
    many_to_many_model.objects.bulk_create(bulk_instances)


def update_product_order_or_mission_forms_from_post(related_attribute_name, many_to_many_form,
                                                    order_or_mission_key, obj, request, many_to_many_model):
    i = 0
    product_orders_or_missions = getattr(obj, related_attribute_name).all()
    for product_order in product_orders_or_missions:
        data = {}
        for key in request.POST:
            if key in many_to_many_form.base_fields:
                value = request.POST.getlist(key)[i]
                if key == "ean":
                    product = Product.objects.filter(ean=value).first()
                    if product:
                        data["product"] = product
                    continue
                data[key] = value
        data[order_or_mission_key] = obj

        if "delete" in request.POST and request.POST.getlist("delete")[i] == "on":
            product_order.delete()
            i += 1
            continue

        for k, v in data.items():
            setattr(product_order, k, v)
        product_order.save()
        i += 1

    for field in many_to_many_form.base_fields:
        amount_forms = len(request.POST.getlist(field))

    if amount_forms - product_orders_or_missions.count() > 0:
        create_product_order_or_mission_forms_from_post(many_to_many_model, many_to_many_form,
                                                        amount_forms - product_orders_or_missions.count(),
                                                        order_or_mission_key, obj, request,
                                                        product_orders_or_missions.count())


def validate_products_are_unique_in_form(POST):
    available_eans = []
    duplicates = []
    for ean in POST.getlist("ean"):
        if ean not in available_eans:
            available_eans.append(ean)
        else:
            duplicates.append(ean)
    if len(duplicates) >= 1:
        return duplicates