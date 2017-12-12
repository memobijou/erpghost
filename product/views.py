from django.shortcuts import render
from django.views.generic import ListView
from .models import Product
from django.http import JsonResponse
from django.core import serializers
import json
# Create your views here.

class ProductListView(ListView):
	def get_queryset(self):
		queryset = Product.objects.all()
		return queryset

	def get_context_data(self, *args, **kwargs):
		context = super(ProductListView, self).get_context_data(*args, **kwargs);
		field_names = []
		meta_fields = Product._meta.get_fields()
		for field in meta_fields:
			field_names.append(field.name)

		rows = []
		for obj in context["object_list"]:
			row = {}
			row[str(obj)] = {}
			rows.append(row)

			for field in meta_fields:
				row[str(obj)][field.name] = getattr(obj, field.name)
		context["field_names"] = field_names
		context["rows"] = rows
		return context