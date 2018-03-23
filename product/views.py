from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import ListView, FormView

from import_excel.funcs import get_table_header, compare_header_with_model_fields, get_records_as_list_with_dicts, \
    check_excel_header_fields_not_in_header, check_excel_for_duplicates
from .models import Product
from order.models import ProductOrder
from utils.utils import get_queries_as_json, set_field_names_onview, \
    handle_pagination, set_paginated_queryset_onview, filter_queryset_from_request, \
    get_and_condition_from_q, get_verbose_names, get_filter_fields, get_table, table_data_to_model
from .serializers import ProductSerializer, IncomeSerializer
from rest_framework.generics import ListAPIView
from rest_framework import generics
from product.forms import ImportForm
from django.urls import reverse_lazy
# Create your views here.
from import_excel.tasks import table_data_to_model_task
from django_celery_results.models import TaskResult
from import_excel.models import TaskDuplicates


class ProductListView(ListView):
    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Product)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Artikel"
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
    success_url = reverse_lazy("product:import")

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["title"] = "Artikelimport"
        context["tasks_results"] = TaskResult.objects.all().order_by("-id")[:10]
        from erpghost import app
        active_tasks = []
        if app.control.inspect().active():
            for k, tasks in app.control.inspect().active().items():
                for task in tasks:
                    active_tasks.append(task["id"])
        context["active_tasks"] = active_tasks
        return context

    def post(self, request, *args, **kwargs):
        content = request.FILES["excel_field"].read()
        file_type = str(request.FILES["excel_field"]).split(".")[1]

        excel_header_fields = ["ean", "hersteller", "part_number"]
        replace_header_fields = {"part_number": "Herstellernummer"}
        related_models = {
            "hersteller": {"app_label": "product", "model_name": "Manufacturer", "verbose_name": "Hersteller"}
        }

        header = get_table_header(file_type, content)

        excel_header_fields_not_in_header = check_excel_header_fields_not_in_header(header, excel_header_fields)

        header_errors = compare_header_with_model_fields(header, Product, excel_header_fields, replace_header_fields=replace_header_fields)

        excel_list = get_records_as_list_with_dicts(file_type, content, header, excel_header_fields,
                                                    replace_header_fields=replace_header_fields)

        if header_errors or excel_header_fields_not_in_header:
            context = self.get_context_data(**kwargs)
            if header_errors:
                context["header_errors"] = header_errors
            if excel_header_fields_not_in_header:
                context["excel_header_fields_not_in_header"] = excel_header_fields_not_in_header
            return render(self.request, self.template_name, context)

        table_data_to_model_task.delay(excel_list, ("product", "Product"), related_models)
        return super().post(request, *args, **kwargs)
