from django.shortcuts import render
from django.views.generic import ListView
from .models import Product
from django.http import JsonResponse
from django.core import serializers
import json
from utils.utils import get_queries_as_json, get_field_names, handle_pagination
from .serializers import ProductSerializer
from rest_framework.generics import ListAPIView
# Create your views here.

class ProductListView(ListView):
	def get_queryset(self):
		queryset = Product.objects.all()
		return queryset

	def get_context_data(self, *args, **kwargs):
		context = super(ProductListView, self).get_context_data(*args, **kwargs);
		context["title"] = "Artikel"

		field_names = []
		context["field_names"] = get_field_names(context["object_list"], ["id"])

		results_per_page = 25

		context["rows"] = get_queries_as_json(context["object_list"])
		context["rows"] = handle_pagination(context["rows"], self.request, results_per_page)["queryset"]
		context["rows"] = [r  for r in context["rows"]]

		pagination_components = handle_pagination(context["object_list"], self.request, results_per_page)
		
		context["object_list"] = pagination_components["queryset"]
		context["pages_range"] = pagination_components["pages_range"]
		context["current_page"] = pagination_components["current_page"]


		return context

class ProductListAPIView(ListAPIView):
	queryset = Product.objects.all()
	serializer_class = ProductSerializer