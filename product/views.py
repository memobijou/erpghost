from django.shortcuts import render
from django.views.generic import ListView
from .models import Product
from django.http import JsonResponse
from django.core import serializers
import json
from utils.utils import get_queries_as_json, set_field_names_onview, handle_pagination, set_paginated_queryset_onview
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

		set_field_names_onview(context["object_list"], ["id"], context)

		set_paginated_queryset_onview(context["object_list"], self.request, 15, context)

		return context

class ProductListAPIView(ListAPIView):
	queryset = Product.objects.all()
	serializer_class = ProductSerializer