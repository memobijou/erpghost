def get_queries_as_json(queryset):
	if not queryset.exists():
		return {}
	Model = queryset[0].__class__
	field_names = []
	meta_fields = Model._meta.get_fields()
	for field in meta_fields:
		field_names.append(field.name)

	rows = []
	for query in queryset:
		row = {}
		row[str(query)] = {}
		rows.append(row)

		for field in meta_fields:
			row[str(query)][field.name] = getattr(query, field.name)
	return rows