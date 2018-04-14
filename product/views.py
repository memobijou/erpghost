from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import DetailView
from django.views.generic import ListView, FormView, UpdateView

from import_excel.funcs import get_table_header, compare_header_with_model_fields, get_records_as_list_with_dicts, \
    check_excel_header_fields_not_in_header, check_excel_for_duplicates
from stock.models import Stock
from .models import Product
from order.models import ProductOrder
from utils.utils import get_queries_as_json, set_field_names_onview, \
    handle_pagination, set_paginated_queryset_onview, filter_queryset_from_request, \
    get_and_condition_from_q, get_verbose_names, get_filter_fields, get_table, table_data_to_model
from .serializers import ProductSerializer, IncomeSerializer
from rest_framework.generics import ListAPIView
from rest_framework import generics
from product.forms import ImportForm, ProductForm, ProductIcecatForm
from django.urls import reverse_lazy
# Create your views here.
from import_excel.tasks import table_data_to_model_task
from django_celery_results.models import TaskResult
from import_excel.models import TaskDuplicates
import pyexcel
from io import BytesIO
import requests
from django.core import files
import base64
import json


class ProductListView(ListView):
    template_name = "product/product_list.html"

    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Product).order_by("-id")
        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Artikel"
        context["fields"] = self.build_fields()
        context["object_list"] = self.get_queryset()
        context["object_list_zip"] = zip(context["object_list"], self.get_product_stocks())
        print(context["object_list"])
        context["filter_fields"] = get_filter_fields(Product, exclude=["id"])
        return context

    def set_pagination(self, queryset):
        page = self.request.GET.get("page")
        paginator = Paginator(queryset, 15)
        if not page:
            page = 1
        current_page_object = paginator.page(int(page))
        return current_page_object

    def get_product_stocks(self):
        queryset = self.get_queryset()
        total_stocks = []
        for q in queryset:
            stock = Stock.objects.filter(ean_vollstaendig=q.ean).first()
            if stock is not None:
                total = stock.total_amount_ean()
                total_stocks.append(total)
            else:
                total_stocks.append("/")
        return total_stocks

    def build_fields(self):
        fields = get_verbose_names(Product, exclude=["id", "short_description", "description", "height", "width",
                                                     "length"])
        fields.append("Bestand")
        fields = [""] + fields
        return fields


class ProductUpdateView(UpdateView):
    form_class = ProductForm

    def get_object(self):
        return Product.objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Artikel bearbeiten"
        return context

    def get_success_url(self):
        return reverse_lazy("product:detail", kwargs={"pk": self.kwargs.get("pk")})


class ProductUpdateIcecatView(ProductUpdateView):
    form_class = ProductIcecatForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["title"] = "Icecat Import"
        user_agent = self.request.META.get('HTTP_USER_AGENT')
        ean = self.object.ean
        ip_address = self.request.META.get('REMOTE_ADDR')
        import os
        app_key = os.environ.get("icecat_app_key")
        shopname = os.environ.get("icecat_username")
        # url = f"https://live.icecat.biz/api/signatures?shopname={shopname}&Language=de&GTIN=8007842706949" \
        #       f"&app_key={app_key}&IP={ip_address}&useragent={user_agent}"
        url = f"https://live.icecat.biz/api/?UserName={shopname}&Language=de&GTIN={ean}" \
              f"&app_key={app_key}"
        response = requests.get(url)
        if response.status_code != requests.codes.ok:
            context["icecat_status"] = "FAIL"
        else:
            context["icecat_status"] = "SUCCESS"
        icecat_response = json.loads(response.text)
        print(url)
        if "data" in icecat_response:
            self.icecat_data_to_form(context["form"], icecat_response.get("data"), context)
            context["icecat"] = icecat_response.get("data").get("GeneralInfo")
        return context

    def icecat_data_to_form(self, form, icecat_json, context):
        title = icecat_json.get("GeneralInfo").get("Title")
        length = None
        width = None
        height = None
        long_description = None
        short_description = None
        brand = None
        image = None

        if "Image" in icecat_json:
            if "HighPic" in icecat_json["Image"]:
                image_url = icecat_json.get("Image").get("HighPic")
                print(image_url)
                r = requests.get(image_url)
                if r.status_code == requests.codes.ok:
                    image_file_bytes = BytesIO()
                    image_file_bytes.write(r.content)
                    encoded_string = base64.b64encode(r.content)
                    context["icecat_image_base64"] = encoded_string
                    context["icecat_image_bytes"] = image_file_bytes
                    filename = image_url.split("/")[-1]
                    context["icecat_image_filename"] = filename

        if "Brand" in icecat_json.get("GeneralInfo"):
            if icecat_json.get("GeneralInfo").get("Brand"):
                brand = icecat_json.get("GeneralInfo").get("Brand")

        if icecat_json.get("GeneralInfo").get("Description"):
            long_description = icecat_json.get("GeneralInfo").get("Description").get("LongDesc")
            print(long_description)
        if icecat_json.get("GeneralInfo").get("SummaryDescription"):
            short_description = icecat_json.get("GeneralInfo").get("SummaryDescription").get("LongSummaryDescription")

        for feature_group in icecat_json.get("FeaturesGroups"):
            feature_name = feature_group.get("FeatureGroup").get("Name").get("Value")

            for feature in feature_group.get('Features'):
                value = feature.get('Value')
                measure_sign = feature.get('Feature').get('Measure').get('Signs').get('_')
                name = feature.get('Feature').get('Name').get('Value')

                if name == "Verpackungshöhe":
                    height = value
                if name == "Verpackungsbreite":
                    width = value
                if name == "Verpackungstiefe":
                    length = value
        if title is not None and title != "":
            form.initial["title"] = title

        if length is not None and length != "":
            form.initial["length"] = length

        if width is not None and width != "":
            form.initial["width"] = width

        if height is not None and height != "":
            form.initial["height"] = height

        if long_description is not None and long_description != "":
            form.initial["description"] = long_description

        if short_description is not None and short_description != "":
            form.initial["short_description"] = short_description

        if brand is not None and brand != "":
            form.initial["brandname"] = brand

    def form_valid(self, form):
        context = self.get_context_data()
        icecat_image_bytes = context["icecat_image_bytes"]
        object = form.save()
        object.main_image.save(context["icecat_image_filename"], files.File(icecat_image_bytes))
        return super().form_valid(form)


class ProductDetailView(DetailView):
    def get_object(self):
        return Product.objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Artikel Detailansicht"
        return context


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
        pk = self.request.query_params.get('id', None)
        if ean is not None:
            queryset = queryset.filter(ean=ean)
        if pk is not None:
            queryset = queryset.filter(id=pk)

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

        excel_header_fields = ["ean", "Hersteller", "part_number", "Artikelname", "short_description", "description",
                               "Markenname"]
        replace_header_fields = {"part_number": "Herstellernummer", "Artikelname": "Titel",
                                 "short_description": "Kurzbeschreibung", "description": "Beschreibung"}
        related_models = {
            #"Hersteller": {"app_label": "product", "model_name": "Manufacturer", "verbose_name": "Hersteller"},
        }

        main_model_related_names = {
            # "Manufacturer": "manufacturer"
        }

        verbose_fields = {"ean": "EAN", "Hersteller": "Hersteller", "part_number": "Herstellernummer",
                          "Artikelname": "Titel", "short_description": "Kurzbeschreibung", "description": "Beschreibung"
                          }

        header = get_table_header(file_type, content)

        # header_errors = compare_header_with_model_fields(header, Product, excel_header_fields,
        #                                                  replace_header_fields=replace_header_fields)

        excel_list = get_records_as_list_with_dicts(file_type, content, header, excel_header_fields,
                                                    replace_header_fields=replace_header_fields)

        # print(f"{header_errors}")

        # if header_errors:
        #     context = self.get_context_data(**kwargs)
        #     if header_errors:
        #         context["header_errors"] = header_errors
        #     return render(self.request, self.template_name, context)

        task = table_data_to_model_task.delay(excel_list, ("product", "Product"), related_models, verbose_fields,
                                              main_model_related_names)
        print(task)
        from celery.result import AsyncResult
        print(AsyncResult("was???").state)
        print(task.state)
        return super().post(request, *args, **kwargs)


class ProductImageImportView(FormView):
    template_name = "product/import.html"
    form_class = ImportForm
    success_url = reverse_lazy("product:import_images")

    def post(self, request, *args, **kwargs):
        bytes = self.request.FILES["excel_field"].read()
        file_type = str(request.FILES["excel_field"]).split(".")[1]
        records = pyexcel.get_records(file_type=file_type, file_content=bytes)
        product_list = []
        for record in records:
            product_list.append((record["EAN"], record["Artikelname"], record["Bild"]))
        print(product_list)
        from product.tasks import upload_images_to_matching_products_task
        upload_images_to_matching_products_task.delay(product_list)
