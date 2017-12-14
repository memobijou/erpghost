from django.utils.dateparse import parse_datetime
import datetime

def get_model_from_queryset(queryset):
	Model = queryset[0].__class__
	return Model

def get_field_names(queryset):
	if not queryset.exists():
		return []
	Model = get_model_from_queryset(queryset)
	meta_fields = Model._meta.get_fields()
	fields = []
	for field in meta_fields:
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
		row[str(query)] = {}
		rows.append(row)
		for field in meta_fields:
			value = getattr(query, field.name)
			print(type(value))
			if isinstance(value, datetime.date):
				print("aaaaaaaa")
				date = value.strftime("%d.%m.%Y")
				# time = value.strftime("%H:%M:%S")
				# value = value.strftime("%d.%m.%Y")
				value = date


			else:
				value = str(value)
			row[str(query)][field.name] = value

	return rows