from django.utils.dateparse import parse_datetime
import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def get_model_from_queryset(queryset):
	Model = queryset[0].__class__
	return Model

def get_field_names(queryset, exclude):
	if not queryset.exists():
		return []
	Model = get_model_from_queryset(queryset)
	meta_fields = Model._meta.get_fields()
	fields = []
	for field in meta_fields:
		if field.name not in exclude:
			fields.append(field.name)
	return fields

def get_meta_field_names(queryset):
	Model = get_model_from_queryset(queryset)
	meta_fields = Model._meta.get_fields()
	return meta_fields

def get_queries_as_json(queryset):
	if not queryset.exists():
		return {}
	Model = get_model_from_queryset(queryset)
	meta_fields = get_meta_field_names(queryset)
	rows = []
	for query in queryset:
		row = {}
		rows.append(row)
		for field in meta_fields:
			value = getattr(query, field.name)
			print(type(value))
			if isinstance(value, datetime.date):
				date = value.strftime("%d.%m.%Y")
				# time = value.strftime("%H:%M:%S")
				# value = value.strftime("%d.%m.%Y")
				value = date


			else:
				value = str(value)
			row[field.name] = value

	return rows

def handle_pagination(queryset, request, results_per_page):
	current_page = request.GET.get("page")
	if(not current_page):
		current_page = 1
	paginator = Paginator(queryset, results_per_page)
	current_object_list = paginator.page(current_page)
	return {"queryset": current_object_list, "pages_range": range(1, paginator.num_pages+1), "current_page": current_page}

def set_paginated_queryset_onview(queryset, request, results_per_page, context):

	context["object_list_as_json"] = get_queries_as_json(context["object_list"])
	context["object_list_as_json"] = handle_pagination(context["object_list_as_json"], request, results_per_page)["queryset"]
	context["object_list_as_json"] = [r  for r in context["object_list_as_json"]]

	pagination_components = handle_pagination(context["object_list"], request, results_per_page)
	
	context["object_list"] = pagination_components["queryset"]
	context["pages_range"] = pagination_components["pages_range"]
	context["current_page"] = pagination_components["current_page"]

def set_field_names_onview(queryset, exclude, context):
	if not exclude:
		exclude = []
	context["field_names"] = get_field_names(context["object_list"], exclude)

