from django.utils.dateparse import parse_datetime
import datetime
from datetime import date
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
import json
from django.db import models


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


def get_field_names(Model, exclude):
	meta_fields = Model._meta.get_fields()
	fields = []
	for field in meta_fields:
		if field.name not in exclude:
			if not field.is_relation and field.related_model is None:
				fields.append(field.name)
	return fields

def get_related_names(Model, exclude):
	meta_fields = Model._meta.get_fields()
	related_fields = []
	for field in meta_fields:
		if field.name not in exclude:
			if field.is_relation and field.related_model and isinstance(field, models.ManyToManyField):
				related_fields.append(field.name)
	return related_fields


def get_meta_field_names(Model):
	meta_fields = Model._meta.get_fields()
	return meta_fields

def get_queries_as_json(queryset):
	if not queryset.exists():
		return {}
	Model = get_model_from_queryset(queryset)
	meta_fields = get_meta_field_names(Model)
	rows = []
	for query in queryset:
		row = get_query_as_json(query)
		rows.append(row)
		# for field in meta_fields:
		# 	# value = getattr(query, field.name)
		# 	# # print(type(value))
		# 	# if isinstance(value, datetime.date):
		# 	# 	date = value.strftime("%d.%m.%Y")
		# 	# 	# time = value.strftime("%H:%M:%S")
		# 	# 	# value = value.strftime("%d.%m.%Y")
		# 	# 	value = date


		# 	# else:
		# 	# 	value = str(value)
		# 	# row[field.name] = value
		# 	row = get_query_as_json(query)
	return rows

def get_query_as_json(query):
	Model = get_model_from_query(query)
	fields = get_field_names(Model, [])

	_dict = {field: getattr(query, field) if not isinstance(getattr(query, field), datetime.date)\
			 else getattr(query, field).strftime("%d.%m.%Y") for field in fields}
	return _dict

def get_related_as_json(query, exclude):
	Model = get_model_from_query(query)
	related_fields = get_related_names(Model, exclude)
	_dict = {k: (getattr(query, k)).all() for k in related_fields if (getattr(query, k)).all().exists()}
	print(str(_dict))
	return _dict


def get_relation_fields(query, exclude,  exclude_relation_fields):
	Model = get_model_from_query(query)
	related_fields = get_related_names(Model, exclude)
	_dict = {k: get_field_names(get_model_from_queryset((getattr(query, k)).all()), exclude_relation_fields[k])\
			 for k in related_fields if (getattr(query, k)).all().exists()}
	return _dict

def handle_pagination(queryset, request, results_per_page):
	if len(queryset) == 0:
		return None
	current_page = request.GET.get("page")
	if(not current_page):
		current_page = 1
	paginator = Paginator(queryset, results_per_page)
	current_object_list = paginator.page(current_page)
	return {"queryset": current_object_list, "pages_range": range(1, paginator.num_pages+1), "current_page": current_page}

def set_paginated_queryset_onview(queryset, request, results_per_page, context):

	context["object_list_as_json"] = get_queries_as_json(context["object_list"])
	if context["object_list_as_json"]:
		context["object_list_as_json"] = handle_pagination(context["object_list_as_json"], request, results_per_page)\
		["queryset"]
	
	context["object_list_as_json"] = [r  for r in context["object_list_as_json"]]

	if context["object_list"]:
		pagination_components = handle_pagination(context["object_list"], request, results_per_page)
	
		context["object_list"] = pagination_components["queryset"]
		context["pages_range"] = pagination_components["pages_range"]
		context["current_page"] = pagination_components["current_page"]


def q_to_dict(q):
	# dict_ = dict(zip(q.keys(), q.values()))
	dict_ = dict(zip(q.keys(), q.values()))
	# print("ta: " + str(json.dumps(q)))
	dict_ = {k: q.getlist(k) if len(q.getlist(k))>1 else v for k, v in q.items()}
	print("bla: " + str(q.urlencode())) #  falls das mal net klappt dann mit q.urlencode zu dictionary umwandeln
	print("bla 2 :" + str(dict(q.lists())))
	return dict_

def get_datatype_model_field(Model, field_name):
	fields = Model._meta.get_fields()
	for f in fields:
		if f.name == field_name:
			return f.get_internal_type()


def set_field_names_onview(qset_or_q, exclude, context, ModelClass):
	if not exclude:
		exclude = []
	if not hasattr(qset_or_q, "__len__"):
		Model = get_model_from_query(qset_or_q)
	else:
		Model = get_model_from_queryset(qset_or_q)
	if not Model:
		Model = ModelClass
	field_names = get_field_names(Model, exclude)
	if field_names == []:
		ModelClass

	field_datatypes = {}
	for field in field_names:
		field_datatypes[field] = get_datatype_model_field(ModelClass, field)
	context["field_datatypes"] = field_datatypes
	context["field_names"] = field_names


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
			print("DUNKY: " + str(type(v)))
			if isinstance(v, list):
				sub_Q = Q()
				for el in v:
					key_condition = k + "__icontains"
					sub_kwargs = {k: el}
					sub_Q |= Q(**sub_kwargs)
				Q_kwargs = None
				print("BUTTLE:   " + str(sub_Q))
			else:
				key_condition =k + "__icontains"
				Q_kwargs = {key_condition: v}
		if Q_kwargs:
			condition &= Q(**Q_kwargs)
		else:
			condition &= sub_Q
	print("BONG: " + str(condition))
	return condition

def filter_queryset_from_request(request, ModelClass):
	querystring = request.GET
	print(str(querystring))

	if len(querystring) == 0:
		return ModelClass.objects.all()

	filter_dict = q_to_dict(querystring)
	# filter_dict = {key: value for key, value in filter_dict.items() if key is not "page"}
	print("wff: "  + str(filter_dict))
	if "page" in filter_dict:
		print("######################")
		filter_dict = {key: val for key, val in filter_dict.items() if key != "page"}
	print(str(filter_dict))
	query_condition = build_query_condition(filter_dict, ModelClass)
	result = ModelClass.objects.filter(query_condition)
	return result


def set_object_ondetailview(context, Model, exclude_fields, exclude_relations, exclude_relation_fields):
	set_field_names_onview(context["object"], exclude_fields, context, Model)
	context["object_as_json"] = get_query_as_json(context["object"])

	context["related_as_json"] = get_related_as_json(context["object"], exclude_relations)
	context["relation_field_names"] = get_relation_fields(context["object"], exclude_relations, exclude_relation_fields)
