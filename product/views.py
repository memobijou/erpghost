from django.shortcuts import render
from django.views.generic import ListView
from .models import Product
from order.models import ProductOrder
from django.http import JsonResponse
from django.core import serializers
import json
from utils.utils import get_queries_as_json, set_field_names_onview,\
handle_pagination, set_paginated_queryset_onview, filter_queryset_from_request,\
get_and_condition_from_q
from .serializers import ProductSerializer,IncomeSerializer
from rest_framework.generics import ListAPIView
import django_filters.rest_framework
from django.db.models import Q
from rest_framework import filters 
from rest_framework import generics
# Create your views here.

class ProductListView(ListView):
	def get_queryset(self):
		# queryset = Product.objects.all()
		queryset = filter_queryset_from_request(self.request, Product)
		print("CHECK FOR EMPTY" + str(queryset))

		return queryset

	def get_context_data(self, *args, **kwargs):
		context = super(ProductListView, self).get_context_data(*args, **kwargs);
		context["title"] = "Artikel"

		set_field_names_onview(context["object_list"], ["id"], context, Product)

		set_paginated_queryset_onview(context["object_list"], self.request, 15, context)
		
		return context



		
class IncomeListView(ListAPIView):
	queryset = ProductOrder.objects.all()
	serializer_class = IncomeSerializer

	def get_queryset(self):

		condition = get_and_condition_from_q(self.request)

		

		queryset = ProductOrder.objects.filter(condition)
        
		return queryset


# class ProductListAPIView(generics.ListAPIView):
# 	queryset = Product.objects.all()
# 	serializer_class = ProductSerializer

class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        """ allow rest api to filter by submissions """
        queryset = Product.objects.all()
        ean = self.request.query_params.get('ean', None)
        myid = self.request.query_params.get('id', None)
        if ean is not None:
            queryset = queryset.filter(ean=ean)
        if myid is not None:
            queryset = queryset.filter(id=myid)
        
        return queryset



        