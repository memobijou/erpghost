import datetime
from datetime import date
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import models

import pyexcel
import collections


# def search_all_wareneingang_products():
#     all_positions = Position.objects.all()
#     wePosition = Position.objects.get(halle="WE")
#     zurPostion = PositionProductOrder.objects.filter(positions=wePosition)
#     gefunden_array = []
#     for pro in zurPostion:
#         count = 0
#         if hasattr(pro.productorder.product, "masterdata"):
#             lastpos = ""
#             while count < pro.amount:
#                 gefunden = False
#                 for p in all_positions:
#                     # print(pro.productorder.product.masterdata.calc_volume)
#                     if (p.available_volume >= pro.productorder.product.masterdata.calc_volume):
#                         if lastpos == p:
#                             myid = PositionProductOrder.objects.latest('id')
#                             save_ = PositionProductOrder.objects.filter(id=myid.id).first()
#                             save_.amount += 1
#                             save_.save()
#                             save_1 = PositionProductOrder.objects.filter(positions=wePosition,productorder=pro.productorder).first()
#                             save_1.amount -= 1
#                             save_1.save()
#                         else:
#                             save_ = PositionProductOrder.objects.filter(positions=wePosition,productorder=pro.productorder).first()
#                             save_.amount -= 1
#                             save_.save()
#                             saveToObjectWE = PositionProductOrder(productorder=pro.productorder, amount=1, status=False,positions=p)
#                             saveToObjectWE.save()
#                         gefunden = True
#                         lastpos = p
#                         gefunden_array.append(saveToObjectWE.id)
#                         break
#                 if gefunden == False:
#                     pass
#                 count = count + 1
#         else:
#             print("kein masterdata")
#
#     return (gefunden_array)
#
# def search_positions_for_order(ordernummer):
#     all_positions = Position.objects.all()
#     wePosition = Position.objects.get(halle="WE")
#     order = Order.objects.get(id=ordernummer)
#     order_products = order.productorder_set.filter(confirmed=True)
#     gefundenarray = []
#     allemyarray = []
#     for pro in order_products:
#         allemyarray.append(pro.id)
#         count = 0
#         if hasattr(pro.product, "masterdata"):
#             lastpos = ""
#             vorhanden = PositionProductOrder.objects.filter(productorder=pro).exists()
#             if vorhanden == False:
#                 while count < pro.real_amount:
#                     gefunden = False
#                     for p in all_positions:
#                         if (p.available_volume >= pro.product.masterdata.calc_volume):
#                             if lastpos == p:
#                                 myid = PositionProductOrder.objects.latest('id')
#                                 save_ = PositionProductOrder.objects.filter(id=myid.id).first()
#                                 save_.amount += 1
#                                 save_.save()
#                             else:
#                                 saveToObject = PositionProductOrder(productorder=pro, amount=1, status=False,
#                                                                     positions=p)
#                                 saveToObject.save()
#                             gefunden = True
#                             lastpos = p
#                             gefundenarray.append(pro.id)
#                             break
#                     if gefunden == False:
#                         if lastpos == wePosition:
#                             myid = PositionProductOrder.objects.latest('id')
#                             save_ = PositionProductOrder.objects.filter(id=myid.id).first()
#                             save_.amount += 1
#                             save_.save()
#                         else:
#                             saveToObjectWE = PositionProductOrder(productorder=pro, amount=1, status=False,
#                                                                   positions=wePosition)
#                             saveToObjectWE.save()
#                         lastpos = wePosition
#                     count = count + 1
#             else:
#                 print("SCHON VORHANDEN")
#         else:
#             print("kein masterdata")
#
#     return (gefundenarray,allemyarray)
#
# def save_picklist(thelist,ordername,position):
#     thelist = list(set(thelist))
#     zurPostion = PositionProductOrder.objects.filter(productorder__in=thelist).exclude(positions=position).exclude(status=True)
#     pickliste = Picklist()
#     pickliste.bestellungsnummer = ordername
#     pickliste.comment = True
#     pickliste.save()
#     myid = Picklist.objects.latest('id')
#     for i in zurPostion:
#         pos = PositionProductOrderPicklist()
#         pos.positionproductorder = i
#         pos.picklist = myid
#         pos.comment = ""
#         pos.pickerid = ""
#         pos.belegt = False
#         pos.save()
#     return zurPostion


class BaseValidationError(ValueError):
    pass


class InvalidDateError(BaseValidationError):
    pass


def validate_date_ddmmyy(day, month, year):
    if month > 12:
        raise InvalidDateError("Oh no wrong month")


def get_model_from_queryset(queryset):
    if len(queryset) > 0:
        Model = get_model_from_query(queryset[0])
    else:
        return None
    return Model


def get_model_from_query(query):
    Model = query.__class__
    return Model


def get_vol_from_columns(Model_Product, Model_Column):
    pos = Model_Product.objects.all()
    products = []
    for x in pos:
        products.append({x: [x.columns.all()]})
        print("HALLOOOO: " + str(products))
        columns_objects = Model_Column.objects.all()
        positions = []
        columns_array = []
        column_data = []
        for col in columns_objects:
            column_data.append(dict({"columns_id": col.id}))
            column_data.append(dict({"columns_gesamt_volumen": col.volumen}))
            amount_pos = len(col.positions.all())
            column_data.append(dict({"total_pos_count": amount_pos}))
            einzelPos = []
            if amount_pos > 0:
                proPos = col.volumen / amount_pos
                for p in col.positions.all():
                    p_products = p.products.all()
                    einzelPos.append(p)
                    einzelPos.append(proPos)
                    # print("einezle postion : " + str(p) + "mit volumen von :" + str(proPos))
                    p_gesamt_vol = 0
                    artikel = []
                    for p_product in p_products:
                        # print("funkzion " + str(get_model_references(p_product,[])))
                        if hasattr(p_product, "masterdata"):
                            vol_artikel = p_product.masterdata.calc_volume()
                            p_gesamt_vol = p_gesamt_vol + vol_artikel
                            artikel.append(p_product)
                            artikel.append(vol_artikel)
                    dif = proPos - p_gesamt_vol
                    # if p_gesamt_vol > proPos:
                    # 	print("ERRRROR weil " + str(dif *-1) + " zu viel")
                    # else:
                    # 	print("frei volumen verfügbar" + str(dif))
                    einzelPos.append(dict({"diff": dif}))
                    einzelPos.append(dict({"artikeln": artikel}))
            # positions.append({col: [col.positions.all()]})
            column_data.append(dict({"GesamtPositionen": einzelPos}))
        columns_array.append(dict({"columns": column_data}))
    # columns_array.append({"col",column_data})
    return columns_array


def get_field_names(Model, exclude=None):
    if exclude == None:
        exclude = []
    meta_fields = Model._meta.get_fields()
    fields = []
    for field in meta_fields:
        if field.name not in exclude:
            # print("DECIDE: "+ str(Model) + " : "  + str(exclude))
            if not field.is_relation and field.related_model is None:
                fields.append(field.name)
    return fields


def get_relation_names(Model, exclude=None, allow_related=None):
    # print(str(allow_related))
    if exclude == None:
        exclude = []
    meta_fields = Model._meta.get_fields()
    relations = []
    for relation in meta_fields:
        if relation.name not in exclude:
            # print("DECIDE: "+ str(Model) + " : "  + str(exclude))
            if (relation.is_relation or relation.related_model) and allow_related == True:
                relations.append(relation.name)
    return relations


def get_property_names(Model, exclude):
    if hasattr(Model, "_meta"):
        property_names = Model._meta._property_names
        return property_names


def get_related_names(Model, exclude):
    meta_fields = Model._meta.get_fields()
    related_fields = []
    for field in meta_fields:
        if field.name not in exclude:
            if field.is_relation and field.related_model and isinstance(field, models.ManyToManyField):
                related_fields.append(field.name)
    return related_fields


def get_model_references(Model, exclude):
    meta_fields = Model._meta.get_fields()
    related_fields = []
    for field in meta_fields:
        if field.name not in exclude:
            if field.one_to_many or (field.many_to_many and \
                                     field.related_model._meta.model_name == field.name):
                key = field.name + "_set"
            else:
                key = field.name
            related_fields.append({"key": key, "name": field.name})
    return related_fields


def get_meta_field_names(Model):
    meta_fields = Model._meta.get_fields()
    return meta_fields


def get_queries_as_json(queryset):
    if queryset and not queryset.exists():
        return {}
    Model = get_model_from_queryset(queryset)
    meta_fields = get_meta_field_names(Model)
    rows = []
    for query in queryset:
        row = get_query_as_json(query)
        rows.append(row)
    return rows


def get_property_values(query):
    model = get_model_from_query(query)
    properties = get_property_names(model, [])
    prop_values = []
    for prop in properties:
        model_function = getattr(query, prop)
        prop_values.append({prop: model_function})
    return prop_values


def get_related_queries(query):
    Model = get_model_from_query(query)
    references = get_model_references(Model, [])
    result = []
    for reference in references:
        if hasattr(query, reference["key"]):
            reference_query = getattr(query, (reference["key"]))
            if hasattr(reference_query, "all"):
                reference_query = reference_query.all()
            result.append({reference["name"]: reference_query})
    return result


def parse_query_to_json(query, fields):
    # print("AHHHHHHHHHHHHHHHHHHHH: " + str(query))
    function_field_values = get_property_values(query)
    parsed_query = {}
    for field in fields:
        if not isinstance(getattr(query, field), datetime.date):
            parsed_query[field] = getattr(query, field)
        else:
            parsed_query[field] = getattr(query, field).strftime("%d.%m.%Y")

    for key_value_pair in function_field_values:
        key, value = next(iter(key_value_pair.items()))
        parsed_query[key] = value
    return parsed_query


def get_query_as_json(query):
    Model = get_model_from_query(query)
    fields = get_field_names(Model, [])
    related_queries = get_related_queries(query)
    _dict = parse_query_to_json(query, fields)
    # print("DOWNLOAD: " + str(related_queries))
    for related_query in related_queries:
        key = next(iter(related_query.keys()))
        val = related_query[key]
        if val.__class__.__name__ == "QuerySet":
            val_queries = []
            for obj in val:
                obj_model = get_model_from_query(obj)
                obj_fields = get_field_names(obj_model, [])
                obj_dict = parse_query_to_json(obj, obj_fields)
                val_queries.append(obj_dict)
            _dict[key] = val_queries
        elif hasattr(val, "_meta"):
            val_model = get_model_from_query(val)
            # print("BLAUUUU: " + str(val_model))
            # print("AUGE: " + str(key) + " : " + str(val))
            val_fields = get_field_names(val_model, [])
            val_dict = parse_query_to_json(val, val_fields)
            _dict[key] = val_dict
        else:
            _dict[key] = val

    # print("HALLO ICH BIN HIER: " + str(_dict))
    return _dict


def get_related_as_json(query, exclude):
    Model = get_model_from_query(query)
    related_fields = get_related_names(Model, exclude)
    _dict = {k: (getattr(query, k)).all() for k in related_fields if (getattr(query, k)).all().exists()}
    print(str(_dict))
    return _dict


def get_relation_fields(query, exclude, exclude_relation_fields):
    Model = get_model_from_query(query)
    related_fields = get_related_names(Model, exclude)
    _dict = {k: get_field_names(get_model_from_queryset((getattr(query, k)).all()), exclude_relation_fields[k]) \
             for k in related_fields if (getattr(query, k)).all().exists()}
    return _dict


def handle_pagination(queryset, request, results_per_page):
    if len(queryset) == 0:
        return None
    current_page = request.GET.get("page")
    if (not current_page):
        current_page = 1
    paginator = Paginator(queryset, results_per_page)
    current_object_list = paginator.page(current_page)
    return {"queryset": current_object_list, "pages_range": range(1, paginator.num_pages + 1),
            "current_page": current_page}


def set_paginated_queryset_onview(queryset, request, results_per_page, context):
    if not context["object_list"]:
        return
    context["object_list_as_json"] = get_queries_as_json(context["object_list"])

    if context["object_list_as_json"]:
        context["object_list_as_json"] = handle_pagination(context["object_list_as_json"], request, results_per_page) \
            ["queryset"]

    context["object_list_as_json"] = [r for r in context["object_list_as_json"]]

    if context["object_list"]:
        pagination_components = handle_pagination(context["object_list"], request, results_per_page)

        context["object_list"] = pagination_components["queryset"]
        context["pages_range"] = pagination_components["pages_range"]
        context["current_page"] = pagination_components["current_page"]
        context["last_page"] = len(context["pages_range"])
        if context["last_page"] != int(context["current_page"]):
            context["next_page"] = str(int(pagination_components["current_page"]) + 1)
        if int(context["current_page"]) > 1 and int(context["current_page"]) != 2:
            context["before_page"] = str(int(pagination_components["current_page"]) - 1)


def q_to_dict(q):
    # dict_ = dict(zip(q.keys(), q.values()))
    dict_ = dict(zip(q.keys(), q.values()))
    # print("ta: " + str(json.dumps(q)))
    dict_ = {k: q.getlist(k) if len(q.getlist(k)) > 1 else v for k, v in q.items()}
    # print("bla: " + str(q.urlencode())) #  falls das mal net klappt dann mit q.urlencode zu dictionary umwandeln
    # print("bla 2 :" + str(dict(q.lists())))
    return dict_


def get_datatype_model_field(Model, field_name):
    fields = Model._meta.get_fields()
    for f in fields:
        if f.name == field_name:
            return f.get_internal_type()


def set_field_names_onview(queryset=None, context=None, ModelClass=None, exclude_fields=None,
                           exclude_filter_fields=None, \
                           template_tagname="field_names", allow_related=None):
    # print(str(allow_related))
    field_names = get_field_names(ModelClass, exclude_fields)
    relation_names = get_relation_names(ModelClass, exclude_fields, allow_related)
    field_names = relation_names + field_names
    context[template_tagname] = field_names
    filter_fields = get_field_names(ModelClass, exclude_filter_fields)
    relation_names = get_relation_names(ModelClass, exclude_fields, allow_related)
    field_names = relation_names + field_names

    context["filter_fields"] = filter_fields
    field_datatypes = {}
    for field in filter_fields:
        field_datatypes[field] = get_datatype_model_field(ModelClass, field)
    context["field_datatypes"] = field_datatypes


def get_date_from_string(date_string, format):
    date_list = date_string.split("/")
    if format == "ddmmyy":
        day, month, year = int(date_list[2]), int(date_list[1]), int(date_list[0])
        try:
            date_ = date(day, month, year)
            return date_
        except ValueError:
            return


def build_query_condition(dict_, Model):
    condition = Q()
    for k, v in dict_.items():
        field_datatype = get_datatype_model_field(Model, k)
        if not v:
            continue
        if field_datatype == "DateField":
            date_ = get_date_from_string(v, "ddmmyy")
            if not date_:
                continue
            Q_kwargs = {k: date_}
        else:
            # print("DUNKY: " + str(type(v)))
            if isinstance(v, list):
                sub_Q = Q()
                for el in v:
                    key_condition = k + "__icontains"
                    sub_kwargs = {k: el}
                    sub_Q |= Q(**sub_kwargs)
                Q_kwargs = None
            # print("BUTTLE:   " + str(sub_Q))
            else:
                key_condition = k + "__icontains"
                Q_kwargs = {key_condition: v}
        if Q_kwargs:
            condition &= Q(**Q_kwargs)
        else:
            condition &= sub_Q
    # print("BONG: " + str(condition))
    return condition


def trim_dict(dict_):
    trimmed_dict = {}

    for key, val in dict_.items():
        print("before strip: " + str(val))
        if isinstance(val, type([])):
            stripped_list = []
            for item in val:
                stripped_list.append(item.strip())
            trimmed_dict[key] = stripped_list
            print("haaaaa: " + str(stripped_list))
        else:
            trimmed_dict[key] = val.strip()
            print("after strip: " + str(val.strip()))

    return trimmed_dict


def filter_queryset_from_request(request, ModelClass):
    querystring = request.GET

    if len(querystring) == 0:
        return ModelClass.objects.all().order_by("-id")

    filter_dict = q_to_dict(querystring)
    filter_dict = trim_dict(filter_dict)
    filter_dict = exclude_non_model_keys_from_dict(filter_dict, ModelClass)
    if "page" in filter_dict:
        filter_dict = {key: val for key, val in filter_dict.items() if key != "page"}
    query_condition = build_query_condition(filter_dict, ModelClass)
    result = ModelClass.objects.filter(query_condition)
    return result


def filter_complete_and_uncomplete_order_or_mission(request, queryset, model_class):
    if request.GET.get("complete"):
        complete_ids = []
        uncomplete_ids = []
        for order_or_mission in queryset:
            is_complete = True
            if hasattr(model_class, "productorder_set"):
                order_or_mission_products = order_or_mission.productorder_set.all()
            elif hasattr(model_class, "productmission_set"):
                order_or_mission_products = order_or_mission.productmission_set.all()
            else:
                return queryset
            for productresolution in order_or_mission_products:
                if productresolution.confirmed is None or productresolution.confirmed is False:
                    is_complete = False
                    uncomplete_ids.append(order_or_mission.id)
                    break
            if is_complete is False:
                continue
            complete_ids.append(order_or_mission.id)
        if request.GET.get("complete") == "VOLLSTÄNDIG":
            queryset = queryset.filter(pk__in=complete_ids)
        elif request.GET.get("complete") == "UNVOLLSTÄNDIG":
            queryset = queryset.filter(pk__in=uncomplete_ids)
    return queryset

def exclude_non_model_keys_from_dict(dict_, model_class):
    tmp_dict = {}
    fields = model_class._meta.get_fields()
    field_names = []
    for field in fields:
        field_names.append(field.name)
    for key, val in dict_.items():
        if key in field_names:
            tmp_dict[key] = val
    dict_ = tmp_dict
    return dict_


def set_object_ondetailview(context=None, ModelClass=None, exclude_fields=None, exclude_relations=None,
                            exclude_relation_fields=None):
    set_field_names_onview(queryset=context["object"], exclude_fields=exclude_fields, context=context,
                           ModelClass=ModelClass)

    context["object_as_json"] = get_query_as_json(context["object"])

    context["related_as_json"] = get_related_as_json(context["object"], exclude_relations)
    context["relation_field_names"] = get_relation_fields(context["object"], exclude_relations, exclude_relation_fields)


def get_and_condition_from_q(request):
    queries = Q()
    for pair in request.query_params:
        # print("LOL 2: " + str(pair))
        # print("LOL 3: " + str(request.query_params[pair]))
        value = request.query_params[pair]
        if pair == "confirmed":
            confirmed = request.query_params.get('confirmed')
            if confirmed == "null":
                value = None
            elif confirmed == "true":
                value = True
            elif confirmed == "false":
                value = False
            else:
                value = None

        queries &= Q(**{pair: value})
    return queries

def get_verbose_names(model_class, exclude=None):
    fields = model_class._meta.get_fields()
    verbose_fields = []
    for field in fields:
        if hasattr(field, "verbose_name") is False:
            continue
        print(field.attname)
        if field.attname not in exclude:
            verbose_fields.append(field.verbose_name)
    return verbose_fields


def get_filter_fields(model_class, exclude=None):
    filter_fields = []
    fields = model_class._meta.get_fields()
    for field in fields:

        if hasattr(field, "verbose_name") is False:
            continue
        if field.attname not in exclude:
            filter_fields.append((field.attname, field.verbose_name))
    return filter_fields


def table_data_to_model(model, table, replace_header=None, limit=None, replace_header_key=None, related_models=None):
    header = table.header
    if replace_header:
        header = replace_header

    bulk_instances = []
    for row in table.content:
        dict_ = {}
        for verbose_name, v in zip(header, row):
            if replace_header_key:
                if replace_header_key.get(verbose_name):
                    print(f"{verbose_name} --- {replace_header_key} --- {get_attname_from_verbose(verbose_name, model)}")
                    verbose_name = replace_header_key.get(verbose_name)

            field_name = get_attname_from_verbose(verbose_name, model)

            related_model = get_relation_from_verbose(verbose_name, model)
            if related_model:
                if related_models:
                    related_model = related_models[verbose_name]
                    new_instance = related_model.objects.create(**{"name": v})
                    v = new_instance

            if limit:
                if verbose_name.lower() in limit:
                    dict_[field_name] = v
            if not limit:
                dict_[field_name] = v
        #print(f"{dict_}")
        bulk_instances.append(model(**dict_))
    model.objects.bulk_create(bulk_instances)


def get_attname_from_verbose(verbose_name, model_class):
    for field in model_class._meta.get_fields():
        if not hasattr(field, "verbose_name"):
            continue
        if field.verbose_name == verbose_name:
            if field.is_relation:
                # model rel rel_class related_model
                # _meta from_db
                return field.attname.replace("_id", "")
            return field.attname
    return verbose_name


def get_relation_from_verbose(verbose_name, model_class):
    for field in model_class._meta.get_fields():
        if not hasattr(field, "verbose_name"):
            continue
        if field.verbose_name == verbose_name:
            if field.is_relation and field.related_model:
                return field.related_model


def is_empty_row(row):
    for col in row:
        if col != "":
            return False
    return True


def get_table_excel(sheet):
    Table = collections.namedtuple('Table', 'header content')
    header = sheet.row[0]
    sheet.name_columns_by_row(0)
    content = []
    for row in sheet.row:
        if is_empty_row(row) is False:
            content.append(row)
    table = Table(header=header, content=content)
    return table


def get_table(content, filetype):
    if filetype == "xlsx":
        sheet = pyexcel.get_sheet(file_type="xlsx", file_content=content)
        table = get_table_excel(sheet)
    elif filetype == "xls":
        sheet = pyexcel.get_sheet(file_type="xls", file_content=content)
        table = get_table_excel(sheet)
    else:
        return
    return table
