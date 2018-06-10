from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView, FormView, UpdateView

from import_excel.funcs import get_table_header, compare_header_with_model_fields, get_records_as_list_with_dicts, \
    check_excel_header_fields_not_in_header, check_excel_for_duplicates
from sku.models import Sku
from stock.models import Stock
from .models import Product, ProductImage, SingleProduct
from order.models import ProductOrder
from utils.utils import get_queries_as_json, set_field_names_onview, \
    handle_pagination, set_paginated_queryset_onview, filter_queryset_from_request, \
    get_and_condition_from_q, get_verbose_names, get_filter_fields, get_table, table_data_to_model
from .serializers import ProductSerializer, IncomeSerializer
from rest_framework.generics import ListAPIView
from rest_framework import generics
from product.forms import ImportForm, ProductForm, ProductIcecatForm, PurchasingPriceForm, SingleProductForm, \
    SingleProductUpdateForm
from django.urls import reverse_lazy
from import_excel.tasks import table_data_to_model_task
from django_celery_results.models import TaskResult
from import_excel.models import TaskDuplicates
import pyexcel
from io import BytesIO
import requests
from django.core import files
import base64
import json
import imghdr


class ProductListView(ListView):
    template_name = "product/product_list.html"

    def get_queryset(self):
        queryset = self.filter_queryset_from_request()
        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Artikel"
        context["fields"] = self.build_fields()
        context["object_list"] = self.get_queryset()
        context["object_list_zip"] = zip(context["object_list"], self.get_product_stocks())
        print(context["object_list"])
        context["filter_fields"] = get_filter_fields(Product, exclude=["id", "main_image", "single_product_id"])
        return context

    def filter_queryset_from_request(self):
        filter_dict = {}
        q_filter = Q()
        for field, verbose_name in self.get_filter_fields(exclude=["main_sku"]):
            if field in self.request.GET:
                GET_value = self.request.GET.get(field)
                if GET_value is not None and GET_value != "":
                    filter_dict[f"{field}__icontains"] = str(self.request.GET.get(field)).strip()

        print(f"OKAYYYY {filter_dict}")

        for item in filter_dict:
            q_filter &= Q(**{item: filter_dict[item]})

        if self.request.GET.get("main_sku") is not None and self.request.GET.get("main_sku") != "":
            sku_value = str(self.request.GET.get("main_sku")).strip()
            print(f"khalid: {sku_value}")
            q_filter &= Q(sku__sku__icontains=sku_value)

        print(q_filter)
        queryset = Product.objects.filter(q_filter).order_by("-id").distinct()
        return queryset

    def get_filter_fields(self, exclude=None):
        filter_fields = []
        fields = Product._meta.get_fields()
        for field in fields:
            if hasattr(field, "verbose_name") is False:
                continue
            if field.attname not in exclude:
                filter_fields.append((field.attname, field.verbose_name))
        return filter_fields

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
            stock = None
            if q.ean is not None and q.ean != "":
                stock = Stock.objects.filter(ean_vollstaendig=q.ean).first()  # wenn kein ean dann nach sku !
            else:
                for sku in q.sku_set.all():
                    stock = Stock.objects.filter(sku=sku.sku).first()
                    if stock is not None:
                        break
            stock_dict = {}
            if stock is not None:
                total = stock.get_available_stocks_of_total_stocks(product=q)
                stock_dict["total"] = total.get('Gesamt')
                stock_dict["total_neu"] = total.get("Neu")
                stock_dict["total_a"] = total.get("A")
                stock_dict["total_b"] = total.get("B")
                stock_dict["total_c"] = total.get("C")
                stock_dict["total_d"] = total.get("D")
                print(stock_dict)
                total_stocks.append(stock_dict)
            else:
                stock_dict["total"] = None
                total_stocks.append(stock_dict)
                print(stock_dict)
        return total_stocks

    def build_fields(self):
        fields = get_verbose_names(Product, exclude=["id", "short_description", "description", "height", "width",
                                                     "length", "main_sku", "single_product_id"])
        fields = [""] + fields
        fields.insert(3, "SKUs")
        fields.insert(7, "Bestand")

        return fields


class ProductUpdateView(UpdateView):
    form_class = ProductForm

    def __init__(self):
        super().__init__()
        self.context = {}
        self.object = None

    def get_object(self):
        self.object = Product.objects.get(pk=self.kwargs.get("pk"))
        return self.object

    def get_context_data(self, **kwargs):
        self.context = super().get_context_data(**kwargs)
        self.context["title"] = "Artikel bearbeiten"
        self.context["purchasing_forms"] = self.initialize_purchasing_forms()
        return self.context

    def initialize_purchasing_forms(self):
        sku_instances = self.get_sku_instances()
        new_sku = sku_instances[0]
        A_sku = sku_instances[1]
        B_sku = sku_instances[2]
        C_sku = sku_instances[3]
        D_sku = sku_instances[4]

        purchasing_forms = [(new_sku.first(), PurchasingPriceForm(data=new_sku.values("purchasing_price").first())),
                            (A_sku.first(), PurchasingPriceForm(data=A_sku.values("purchasing_price").first())),
                            (B_sku.first(), PurchasingPriceForm(data=B_sku.values("purchasing_price").first())),
                            (C_sku.first(), PurchasingPriceForm(data=C_sku.values("purchasing_price").first())),
                            (D_sku.first(), PurchasingPriceForm(data=D_sku.values("purchasing_price").first()))]
        return purchasing_forms

    def get_success_url(self):
        return reverse_lazy("product:detail", kwargs={"pk": self.kwargs.get("pk")})

    def form_valid(self, form):
        more_images = self.request.FILES.getlist("more_images")
        validation_msg = self.validate_files_are_images(more_images)
        purchasing_prices_forms = self.get_purchasing_prices_forms()
        purchasing_prices_forms_are_valid = self.validate_purchasing_prices_forms(purchasing_prices_forms)

        if validation_msg is True and purchasing_prices_forms_are_valid is True:
            self.delete_checked_images(self.request.POST.getlist("to_delete_more_images"))
            self.upload_more_images(more_images)
            self.update_sku_purchasing_prices()
        else:
            if validation_msg is not True:
                form.add_error('more_images', validation_msg)
            self.context["form"] = form
            self.context["purchasing_forms"] = purchasing_prices_forms
            self.context["title"] = "Artikel bearbeiten"
            return render(self.request, "product/product_form.html", self.context)
        return super().form_valid(form)

    def get_purchasing_prices_forms(self):
        post_forms = []

        for purchasing_price in self.request.POST.getlist("purchasing_price"):
            purchasing_price_form = PurchasingPriceForm(data={"purchasing_price": purchasing_price})
            post_forms.append(purchasing_price_form)

        purchasing_price_forms = []
        print(purchasing_price_forms)
        for sku, price in zip(self.get_sku_instances(), post_forms):
            purchasing_price_forms.append((sku, price))
        return purchasing_price_forms

    def validate_purchasing_prices_forms(self, purchasing_forms):
        is_valid = True
        for sku, price_form in purchasing_forms:
            if price_form.is_valid() is False:
                is_valid = False
                break
        if is_valid is True:
            return True
        else:
            return False

    def get_sku_instances(self):
        new_sku = Sku.objects.filter(product_id=self.object.pk, state="Neu")
        A_sku = Sku.objects.filter(product_id=self.object.pk, state="A")
        B_sku = Sku.objects.filter(product_id=self.object.pk, state="B")
        C_sku = Sku.objects.filter(product_id=self.object.pk, state="C")
        D_sku = Sku.objects.filter(product_id=self.object.pk, state="D")
        return [new_sku, A_sku, B_sku, C_sku, D_sku]

    def update_sku_purchasing_prices(self):
        print(self.object)
        for sku, purchasing_price in zip(self.object.sku_set.all().order_by("sku"),
                                         self.request.POST.getlist("purchasing_price")):
            if purchasing_price is not None and purchasing_price != "":
                sku.purchasing_price = float(purchasing_price)
                sku.save()
            else:
                sku.purchasing_price = None
                sku.save()
        print(self.request.POST)

    def validate_files_are_images(self, more_images):
        msg = f"Folgende Dateien sind keine Bilder: \n"
        non_image_files = []
        for file in more_images:
            if imghdr.what(file) is None:
                non_image_files.append(file)
                msg += f"{str(file)},\n"
        if len(non_image_files) > 0:
            msg = msg[:-2]
            return msg
        return True

    def upload_more_images(self, more_images):
        for image in more_images:
            img_object = ProductImage(image=image, product_id=self.object.pk)
            img_object.save()

    def delete_checked_images(self, checked_images_ids):
        ProductImage.objects.filter(pk__in=checked_images_ids).delete()


class ProductCreateView(CreateView):
    form_class = ProductForm
    template_name = "product/product_form.html"

    def __init__(self):
        super().__init__()
        self.context = {}
        self.object = None

    def get_context_data(self, **kwargs):
        self.context = super().get_context_data(**kwargs)
        self.context["title"] = "Neuen Artikel anlegen"
        self.context["purchasing_forms"] = self.initialize_purchasing_forms()
        return self.context

    def initialize_purchasing_forms(self):
        purchasing_forms = [(None, PurchasingPriceForm()), (None, PurchasingPriceForm()), (None, PurchasingPriceForm()),
                            (None, PurchasingPriceForm()), (None, PurchasingPriceForm())]
        return purchasing_forms

    def form_valid(self, form):
        more_images = self.request.FILES.getlist("more_images")
        validation_msg = self.validate_files_are_images(more_images)
        purchasing_prices_forms = self.get_purchasing_prices_forms()

        purchasing_prices_forms_are_valid = self.validate_purchasing_forms(purchasing_prices_forms)

        if validation_msg is True and purchasing_prices_forms_are_valid is True:
            self.object = form.save(commit=True)
            self.create_sku_purchasing_prices()
            self.upload_more_images(more_images)
        else:
            if validation_msg is not True:
                form.add_error('more_images', validation_msg)
            self.context["purchasing_forms"] = purchasing_prices_forms
            self.context["form"] = form
            self.context["title"] = "Artikel bearbeiten"
            return render(self.request, self.template_name, self.context)
        return HttpResponseRedirect(self.get_success_url())

    def create_sku_purchasing_prices(self):
        for sku, purchasing_price in zip(self.object.sku_set.all().order_by("sku"),
                                         self.request.POST.getlist("purchasing_price")):
            if purchasing_price is not None and purchasing_price != "":
                sku.purchasing_price = float(purchasing_price)
                sku.save()
            else:
                sku.purchasing_price = None
                sku.save()

    def get_purchasing_prices_forms(self):
        post_forms = []

        for purchasing_price in self.request.POST.getlist("purchasing_price"):
            purchasing_price_form = PurchasingPriceForm(data={"purchasing_price": purchasing_price})
            post_forms.append(purchasing_price_form)

        purchasing_price_forms = []
        print(purchasing_price_forms)
        for sku, price in zip([None, None, None, None, None], post_forms):
            purchasing_price_forms.append((sku, price))
        return purchasing_price_forms

    def validate_purchasing_forms(self, purchasing_forms):
        is_valid = True
        for sku, price_form in purchasing_forms:
            if price_form.is_valid() is False:
                is_valid = False
                break
        if is_valid is True:
            return True
        else:
            return False

    def validate_files_are_images(self, more_images):
        msg = f"Folgende Dateien sind keine Bilder: \n"
        non_image_files = []
        for file in more_images:
            if imghdr.what(file) is None:
                non_image_files.append(file)
                msg += f"{str(file)},\n"
        if len(non_image_files) > 0:
            msg = msg[:-2]
            return msg
        return True

    def upload_more_images(self, more_images):
        for image in more_images:
            img_object = ProductImage(image=image, product_id=self.object.pk)
            img_object.save()


class ProductSingleCreateView(CreateView):
    form_class = SingleProductForm
    template_name = "product/product_single_form.html"

    def __init__(self):
        super().__init__()
        self.object = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Einzelartikel anlegen"
        return context

    def form_valid(self, form, **kwargs):
        self.object = form.save(commit=False)
        self.set_product_to_single_product(form.data)

        more_images = self.request.FILES.getlist("more_images")
        validation_msg = self.validate_files_are_images(more_images)

        if validation_msg is True:
            self.upload_more_images(more_images)
        else:
            context = self.get_context_data(**kwargs)

            if validation_msg is not True:
                form.add_error('more_images', validation_msg)

            context["form"] = form
            context["title"] = "Artikel bearbeiten"
            return render(self.request, "product/product_single_form.html", context)
        return HttpResponseRedirect(reverse_lazy("product:detail", kwargs={"pk": self.object.pk}))

    def set_product_to_single_product(self, data):
        single_product = SingleProduct()
        single_product.save()
        self.object.single_product = single_product
        self.object.save()
        state = data.get("state")
        if state == "Neu":
            state = ""
        sku_instance = Sku(product_id=self.object.pk, sku=f"{state}{self.object.main_sku}", state=state)
        sku_instance.save()
        self.object.sku_set.add(sku_instance)
        self.object.save()

    def validate_files_are_images(self, more_images):
        msg = f"Folgende Dateien sind keine Bilder: \n"
        non_image_files = []
        for file in more_images:
            if imghdr.what(file) is None:
                non_image_files.append(file)
                msg += f"{str(file)},\n"
        if len(non_image_files) > 0:
            msg = msg[:-2]
            return msg
        return True

    def upload_more_images(self, more_images):
        for image in more_images:
            img_object = ProductImage(image=image, product_id=self.object.pk)
            img_object.save()


class ProductSingleUpdateView(UpdateView):
    form_class = SingleProductUpdateForm
    template_name = "product/product_single_form.html"

    def __init__(self):
        super().__init__()
        self.object = None

    def get_object(self, queryset=None):
        self.object = Product.objects.get(pk=self.kwargs.get("pk"))
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["title"] = f"Einzelartikel {self.object.sku_set.first().sku} bearbeiten"
        return context

    def form_valid(self, form, **kwargs):
        more_images = self.request.FILES.getlist("more_images")
        validation_msg = self.validate_files_are_images(more_images)

        if validation_msg is True:
            self.delete_checked_images(self.request.POST.getlist("to_delete_more_images"))
            self.object = form.save(commit=True)
            self.upload_more_images(more_images)
        else:
            if validation_msg is not True:
                form.add_error('more_images', validation_msg)
            context = self.get_context_data(**kwargs)
            context["form"] = form
            return render(self.request, self.template_name, context)
        return HttpResponseRedirect(reverse_lazy("product:detail", kwargs={"pk": self.object.pk}))

    def validate_files_are_images(self, more_images):
        msg = f"Folgende Dateien sind keine Bilder: \n"
        non_image_files = []
        for file in more_images:
            if imghdr.what(file) is None:
                non_image_files.append(file)
                msg += f"{str(file)},\n"
        if len(non_image_files) > 0:
            msg = msg[:-2]
            return msg
        return True

    def upload_more_images(self, more_images):
        for image in more_images:
            img_object = ProductImage(image=image, product_id=self.object.pk)
            img_object.save()

    def delete_checked_images(self, checked_images_ids):
        ProductImage.objects.filter(pk__in=checked_images_ids).delete()


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy("product:list")
    template_name = "product/product_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["Title"] = "Artikel löschen"
        context["delete_items"] = self.get_object()
        return context

    def get_object(self, queryset=None):
        return Product.objects.filter(id__in=self.request.GET.getlist('item'))


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
    def __init__(self):
        super().__init__()
        self.object = None
        self.context = {}

    def get_object(self):
        return Product.objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        self.context = super().get_context_data(**kwargs)
        self.context["title"] = "Artikel Detailansicht"
        self.context["stock"] = self.get_product_stocks()
        self.context["product_skus"] = self.object.sku_set.all().order_by('pk')
        return self.context

    def get_product_stocks(self):
        stock = None
        query = self.get_object()
        if query.ean is not None and query.ean != "":
            stock = Stock.objects.filter(ean_vollstaendig=query.ean).first()
        else:
            for sku in query.sku_set.all():
                stock = Stock.objects.filter(sku=sku.sku).first()
                if stock is not None:
                    break

        stock_dict = {}

        if stock is not None:
            total = stock.get_available_stocks_of_total_stocks()
            stock_dict["total"] = total.get('Gesamt')
            stock_dict["total_neu"] = total.get("Neu")
            stock_dict["total_a"] = total.get("A")
            stock_dict["total_b"] = total.get("B")
            stock_dict["total_c"] = total.get("C")
            stock_dict["total_d"] = total.get("D")
        else:
            stock_dict["total"] = None
        return stock_dict


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
        sku = self.request.query_params.get('sku', None)
        pk = self.request.query_params.get('id', None)
        if ean is not None:
            queryset = queryset.filter(ean=ean)
        if pk is not None:
            queryset = queryset.filter(id=pk)
        if sku is not None:
            queryset = queryset.filter(sku__sku=sku)

        if sku is not None and ean is not None:
            queryset = Product.objects.filter(Q(sku__sku=ean) | Q(ean=ean) | Q(sku__sku=sku) | Q(ean=sku))
        return queryset[:15]


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
