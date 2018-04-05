from django.shortcuts import render
from django.views.generic import ListView

from product.models import Product
from .models import Warehouse
from django.http import JsonResponse
from django.core import serializers
import json
from utils.utils import get_queries_as_json, set_field_names_onview, \
    handle_pagination, set_paginated_queryset_onview, filter_queryset_from_request
from .serializers import WarehouseSerializer
from rest_framework.generics import ListAPIView
import django_filters.rest_framework
from django.db.models import Q
from rest_framework import filters
from rest_framework import generics
from django.shortcuts import render  # prober sehr gut mistgeburt mach


# Create your views here.

# khalas teste mal
def blabla1(request):
    queryset = Warehouse.objects.all()
    return render(request, "warehouse/blabla.html", {"object_list": queryset})


# Create your views here.
class WarehouseListView(ListView):
    def get_queryset(self):
        queryset = Warehouse.objects.all()
        return queryset


class WarehouseListAPIView(generics.ListAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

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
