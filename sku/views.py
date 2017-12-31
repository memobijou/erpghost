from django.shortcuts import render
from django.views.generic import ListView
from .models import Sku
from django.http import JsonResponse
from django.core import serializers
import json
from utils.utils import get_queries_as_json, set_field_names_onview,\
handle_pagination, set_paginated_queryset_onview, filter_queryset_from_request
from rest_framework.generics import ListAPIView
import django_filters.rest_framework
from django.db.models import Q
from rest_framework import filters 
from rest_framework import generics

def hallo():
	obj = Sku.objects.all()
	return obj


class SkuListView(ListView):
	def get_queryset(self):
		queryset = Sku.objects.all()
		# queryset = filter_queryset_from_request(self.request, Sku)
		# print("CHECK FOR EMPTY" + str(queryset))

		return queryset
		
def get_context_data(self, *args, **kwargs):
		# context = super(ProductListView, self).get_context_data(*args, **kwargs);
		context["test"] = hallo()

		set_field_names_onview(context["object_list"], context)

		set_paginated_queryset_onview(context["object_list"], self.request, 15, context)
		
		return context
