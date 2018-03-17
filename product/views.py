from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import ListView, FormView
from .models import Product, Manufacturer
from order.models import ProductOrder
from django.http import JsonResponse
from django.core import serializers
import json
from utils.utils import get_queries_as_json, set_field_names_onview, \
    handle_pagination, set_paginated_queryset_onview, filter_queryset_from_request, \
    get_and_condition_from_q, get_verbose_names, get_filter_fields, get_table, table_data_to_model, \
    compare_header_with_model_fields
from .serializers import ProductSerializer, IncomeSerializer
from rest_framework.generics import ListAPIView
import django_filters.rest_framework
from django.db.models import Q
from rest_framework import filters
from rest_framework import generics
from product.forms import ImportForm
from django.urls import reverse_lazy
from celery.decorators import task
# Create your views here.

@task()
def celery_test():
    print("CELERY IS COOL")


class ProductListView(ListView):
    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Product)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Artikel"
        celery_test.delay()
        context["fields"] = get_verbose_names(Product, exclude=["id"])
        context["object_list"] = self.set_pagination()
        context["filter_fields"] = get_filter_fields(Product, exclude=["id"])
        return context

    def set_pagination(self):
        page = self.request.GET.get("page")
        paginator = Paginator(self.get_queryset(), 15)
        if not page:
            page = 1
        current_page_object = paginator.page(page)
        return current_page_object

class IncomeListView(ListAPIView):
    queryset = ProductOrder.objects.all()
    serializer_class = IncomeSerializer

    def get_queryset(self):
        condition = get_and_condition_from_q(self.request)

        queryset = ProductOrder.objects.filter(condition)

        return queryset


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

class ProductImportView(FormView):
    template_name = "product/import.html"
    form_class = ImportForm
    success_url = reverse_lazy("product:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["title"] = "Artikelimport"
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        content = request.FILES["excel_field"].read()
        file_type = str(request.FILES["excel_field"]).split(".")[1]
        table = get_table(content, file_type)
        limit = ["ean", "hersteller", "herstellernummer"]
        error_fields = compare_header_with_model_fields(table.header, Product, limit=limit)

        if error_fields:
            context["error_fields"] = error_fields
            return render(request, self.template_name, context)

        table_data_to_model(Product, table, limit=limit, replace_header_key={"part_number": "Herstellernummer"},
                            related_models={"Hersteller": Manufacturer})
        return super().post(request, *args, **kwargs)

