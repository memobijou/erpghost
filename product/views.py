from django.shortcuts import render
from django.views.generic import ListView
from .models import Product
from django.http import JsonResponse
from django.core import serializers
import json
from utils.utils import get_queries_as_json, get_field_names
# Create your views here.

class ProductListView(ListView):
	def get_queryset(self):
		queryset = Product.objects.all()
		return queryset

	def get_context_data(self, *args, **kwargs):
		context = super(ProductListView, self).get_context_data(*args, **kwargs);
		
		field_names = []

		rows = get_queries_as_json(context["object_list"])
		print(str(rows))
		context["field_names"] = get_field_names(context["object_list"])
		context["rows"] = rows
		return context