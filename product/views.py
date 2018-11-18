from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView, FormView, UpdateView

from mission.models import Mission, ProductMission
from online.forms import OnlineSkuForm, OfferForm
from import_excel.funcs import get_table_header, compare_header_with_model_fields, get_records_as_list_with_dicts, \
    check_excel_header_fields_not_in_header, check_excel_for_duplicates
from sku.models import Sku
from stock.models import Stock
from .models import Product, ProductImage, SingleProduct, get_states_totals_and_total
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
from django.db.models import Case, When, Value, IntegerField, Sum


class ProductListBaseView(LoginRequiredMixin, ListView):
    paginate_by = 30

    def __init__(self):
        self.context = {}
        super().__init__()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.context)
        print(f"wwww: {context}")
        context["title"] = "Artikel Übersicht"
        object_list = context["object_list"]
        context["product_list"] = self.get_product_list(object_list)
        return context

    def get_product_list(self, object_list):
        product_list = []
        for obj in object_list:
            all_skus = obj.sku_set.all()
            main_skus = all_skus.filter(main_sku=True).order_by("state")
            online_skus = all_skus.filter(main_sku__isnull=True).order_by("state")

            states_totals, total = get_states_totals_and_total(obj, all_skus)
            product_list.append((obj, main_skus, online_skus, states_totals, total))
        return product_list

    def get_queryset(self):
        print(f"hey ho: {self.queryset}")
        order_by_amount = self.get_value_from_GET_or_session("order_by_amount", self.request)
        if order_by_amount == "down":
            self.queryset = self.queryset.annotate(
                total_stock=Sum("stock__bestand")).annotate(
                nulls_last=Case(When(total_stock=None, then=Value(0)), output_field=IntegerField())
            ).order_by("-nulls_last", "-total_stock")
        elif order_by_amount == "up":
            self.queryset = self.queryset.annotate(
                total_stock=Sum("stock__bestand")).annotate(
                nulls_last=Case(When(total_stock=None, then=Value(0)), output_field=IntegerField())
            ).order_by("nulls_last", "total_stock")

        print(f"test: {self.request.GET.get('q')}")

        q = self.get_value_from_GET_or_session("q", self.request)

        ean = self.get_value_from_GET_or_session("ean", self.request)
        if ean != "":
            self.queryset = self.queryset.filter(ean__icontains=ean)

        sku = self.get_value_from_GET_or_session("sku", self.request)
        if sku != "":
            self.queryset = self.queryset.filter(sku__sku__icontains=sku)

        title = self.get_value_from_GET_or_session("title", self.request)
        if title != "":
            self.queryset = self.queryset.filter(title__icontains=title)

        manufacturer = self.get_value_from_GET_or_session("manufacturer", self.request)
        if manufacturer != "":
            self.queryset = self.queryset.filter(manufacturer__icontains=manufacturer)

        brandname = self.get_value_from_GET_or_session("brandname", self.request)
        if brandname != "":
            self.queryset = self.queryset.filter(brandname__icontains=brandname)

        part_number = self.get_value_from_GET_or_session("part_number", self.request)
        if part_number != "":
            self.queryset = self.queryset.filter(part_number__icontains=part_number)

        short_description = self.get_value_from_GET_or_session("short_description", self.request)
        if short_description != "":
            self.queryset = self.queryset.filter(short_description__icontains=short_description)

        long_description = self.get_value_from_GET_or_session("description", self.request)
        if long_description != "":
            self.queryset = self.queryset.filter(description__icontains=long_description)

        self.context = {"product_q": q, "product_ean": ean, "product_sku": sku, "product_title": title,
                        "product_manufacturer": manufacturer, "product_brandname": brandname,
                        "product_part_number": part_number, "product_short_description": short_description,
                        "product_long_description": long_description, "product_order_by_amount": order_by_amount}

        self.context = self.set_filter_and_search_values_in_context(q, ean, sku, title, manufacturer, brandname,
                                                                    part_number, short_description, long_description,
                                                                    order_by_amount)

        if q is not None and q != "":
            q_list = q.split()
            ean_q = Q()
            title_q = Q()
            short_description_q = Q()
            long_description_q = Q()
            sku_q = Q()
            brandname_q = Q()
            manufacturer_q = Q()
            part_number_q = Q()
            asin_q = Q()

            print(q_list)
            for q_element in q_list:
                q_element = q_element.strip()

                ean_q &= Q(ean__icontains=q_element)
                title_q &= Q(title__icontains=q_element)
                short_description_q &= Q(short_description__icontains=q_element)
                long_description_q &= Q(description__icontains=q_element)
                sku_q &= Q(sku__sku__icontains=q_element)
                brandname_q &= Q(brandname__icontains=q_element)
                manufacturer_q &= Q(manufacturer__icontains=q_element)
                part_number_q &= Q(part_number__icontains=q_element)
                asin_q &= Q(sku__asin__icontains=q_element)

            self.queryset = self.queryset.filter(Q(ean_q | title_q | short_description_q | long_description_q |
                                                   sku_q | brandname_q | manufacturer_q | part_number_q | asin_q))
        print(f"banana: {self.queryset}")
        return self.queryset.distinct()

    def get_value_from_GET_or_session(self, value, request):
        pass

    def set_filter_and_search_values_in_context(self, q, ean, sku, title, manufacturer, brandname, part_number,
                                                short_description, long_descripton, order_by_amount):
        pass


class ProductListView(ProductListBaseView):
    template_name = "product/product_list.html"
    paginate_by = 30
    queryset = Product.objects.filter(single_product__isnull=True)

    def __init__(self):
        self.context = {}
        super().__init__()

    def dispatch(self, request, *args, **kwargs):
        if self.request.GET.get("clear_filter", "") or "" == "1":
            filter_values = {"product_q": None, "product_ean": None, "product_sku": None, "product_title": None,
                             "product_manufacturer": None, "product_brandname": None,
                             "product_part_number": None, "product_short_description": None,
                             "product_long_description": None, "product_order_by_amount": None}
            print(f"bibi: {filter_values}")
            for name, value in filter_values.items():
                request.session[name] = value
        return super().dispatch(request, *args, **kwargs)

    def set_filter_and_search_values_in_context(self, q, ean, sku, title, manufacturer, brandname, part_number,
                                                short_description, long_descripton, order_by_amount):
        self.context = {"product_q": q, "product_ean": ean, "product_sku": sku, "product_title": title,
                        "product_manufacturer": manufacturer, "product_brandname": brandname,
                        "product_part_number": part_number, "product_short_description": short_description,
                        "product_long_description": long_descripton, "product_order_by_amount": order_by_amount}
        print("UND ???????")
        return self.context

    def get_value_from_GET_or_session(self, value, request):
        get_value = request.GET.get(value)
        if get_value is not None:
            request.session[f"product_{value}"] = get_value.strip()
            return get_value
        else:
            if request.GET.get("q") is None:
                return request.session.get(f"product_{value}", "") or ""
            else:
                request.session[f"product_{value}"] = ""
                return ""


class ProductListViewDEAD(ListView):
    template_name = "product/product_list.html"

    def get_queryset(self):
        queryset = self.filter_queryset_from_request()

        if "order_by_amount" in self.request.GET and self.request.GET.get("order_by_amount") == "down":
            queryset = queryset.values_as_instances().annotate(total_stock=Sum("stock__bestand")).\
                annotate(nulls_last=Case(When(total_stock=None, then=Value(0)),
                                         output_field=IntegerField())).order_by("-nulls_last", "-total_stock")

        if "order_by_amount" in self.request.GET and self.request.GET.get("order_by_amount") == "up":
            queryset = queryset.values_as_instances().annotate(total_stock=Sum("stock__bestand")).\
                annotate(nulls_last=Case(When(total_stock=None, then=Value(0)), output_field=IntegerField())).\
                order_by("nulls_last", "total_stock")

        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Artikel"
        context["fields"] = self.build_fields()
        context["object_list"] = self.get_queryset()
        context["object_list_zip"] = zip(context["object_list"], self.get_product_stocks())
        context["order_by_amount"] = self.request.GET.get("order_by_amount")
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

        for item in filter_dict:
            q_filter &= Q(**{item: filter_dict[item]})

        if self.request.GET.get("main_sku") is not None and self.request.GET.get("main_sku") != "":
            sku_value = str(self.request.GET.get("main_sku")).strip()
            q_filter &= Q(sku__sku__icontains=sku_value)

        search_filter = Q()
        search_value = self.request.GET.get("q")

        if search_value is not None and search_value != "":
            search_filter |= Q(**{f"ean__icontains": search_value.strip()})
            search_filter |= Q(sku__sku__icontains=search_value.strip())
            search_filter |= Q(title__icontains=search_value.strip())
            search_filter |= Q(brandname__icontains=search_value.strip())
            search_filter |= Q(manufacturer__icontains=search_value.strip())
            search_filter |= Q(part_number__icontains=search_value.strip())
            search_filter |= Q(short_description__icontains=search_value.strip())
            search_filter |= Q(description__icontains=search_value.strip())

        q_filter &= search_filter

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
                print(stock)
                if stock is None or stock == "":
                    for sku in q.sku_set.all():
                        stock = Stock.objects.filter(sku=sku.sku).first()
                        if stock is not None:
                            break
            else:
                for sku in q.sku_set.all():
                    stock = Stock.objects.filter(sku=sku.sku).first()
                    if stock is not None:
                        break
                print(stock)
            stock_dict = {}
            if stock is not None:
                total = stock.get_available_stocks_of_total_stocks(product=q)
                stock_dict["total"] = total.get('Gesamt')
                stock_dict["total_neu"] = total.get("Neu")
                stock_dict["total_g"] = total.get("G")
                stock_dict["total_b"] = total.get("B")
                stock_dict["total_c"] = total.get("C")
                stock_dict["total_d"] = total.get("D")
                total_stocks.append(stock_dict)
            else:
                stock_dict["total"] = None
                total_stocks.append(stock_dict)
            print(f"bandi: {stock_dict} - {q.ean}")
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
        self.sku_instances = None

    def get_object(self):
        self.object = Product.objects.get(pk=self.kwargs.get("pk"))
        self.sku_instances = self.get_sku_instances()
        return self.object

    def get_context_data(self, **kwargs):
        self.context = super().get_context_data(**kwargs)
        self.context["title"] = "Artikel bearbeiten"
        self.context["purchasing_forms"] = self.initialize_purchasing_forms()
        return self.context

    def initialize_purchasing_forms(self):
        new_sku = self.sku_instances[0]
        b_sku = self.sku_instances[1]
        c_sku = self.sku_instances[2]
        d_sku = self.sku_instances[3]
        g_sku = self.sku_instances[4]

        purchasing_forms = [
                        (new_sku, PurchasingPriceForm(data={"purchasing_price": new_sku.purchasing_price})),
                        (b_sku, PurchasingPriceForm(data={"purchasing_price": b_sku.purchasing_price})),
                        (c_sku, PurchasingPriceForm(data={"purchasing_price": c_sku.purchasing_price})),
                        (d_sku, PurchasingPriceForm(data={"purchasing_price": d_sku.purchasing_price})),
                        (g_sku, PurchasingPriceForm(data={"purchasing_price": g_sku.purchasing_price})),
                    ]
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
        for sku, price in zip(self.sku_instances, post_forms):
            purchasing_price_forms.append((sku, price))
        print(purchasing_price_forms)
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
        new_sku = Sku.objects.filter(product_id=self.object.pk, state="Neu").first()
        b_sku = Sku.objects.filter(product_id=self.object.pk, state="B").first()
        c_sku = Sku.objects.filter(product_id=self.object.pk, state="C").first()
        d_sku = Sku.objects.filter(product_id=self.object.pk, state="D").first()
        g_sku = Sku.objects.filter(product_id=self.object.pk, state="G").first()
        return [new_sku, b_sku, c_sku, d_sku, g_sku]

    def update_sku_purchasing_prices(self):
        print(self.object)
        sku_instances = self.sku_instances
        for sku, purchasing_price in zip(sku_instances, self.request.POST.getlist("purchasing_price")):
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
        for sku, purchasing_price in zip(self.get_sku_instances(),
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

    def get_sku_instances(self):
        new_sku = Sku.objects.filter(product_id=self.object.pk, state="Neu").first()
        B_sku = Sku.objects.filter(product_id=self.object.pk, state="B").first()
        C_sku = Sku.objects.filter(product_id=self.object.pk, state="C").first()
        D_sku = Sku.objects.filter(product_id=self.object.pk, state="D").first()
        G_sku = Sku.objects.filter(product_id=self.object.pk, state="G").first()
        return [new_sku, B_sku, C_sku, D_sku, G_sku]


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
            prefix = "N"
        else:
            prefix = state

        purchasing_price = data.get("purchasing_price")

        sku_instance = Sku(product_id=self.object.pk, sku=f"{prefix}{self.object.main_sku}", state=state,
                           purchasing_price=purchasing_price)
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
        self.sku = None

    def get_object(self, queryset=None):
        self.object = Product.objects.get(pk=self.kwargs.get("pk"))
        self.sku = self.object.sku_set.first()
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["title"] = f"Einzelartikel {self.sku.sku} bearbeiten"
        return context

    def get_form(self, form_class=None):
        form = super().get_form()
        form.initial["purchasing_price"] = self.sku.purchasing_price
        return form

    def form_valid(self, form, **kwargs):
        more_images = self.request.FILES.getlist("more_images")
        validation_msg = self.validate_files_are_images(more_images)

        if validation_msg is True:
            self.delete_checked_images(self.request.POST.getlist("to_delete_more_images"))
            self.object = form.save(commit=True)

            purchasing_price = self.request.POST.get("purchasing_price")

            if purchasing_price is not None and purchasing_price != "":
                self.sku.purchasing_price = float(purchasing_price)
            else:
                print(self.sku.purchasing_price)
                self.sku.purchasing_price = None

            self.sku.save()

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
    template_name = "product/product_detail.html"

    def __init__(self):
        super().__init__()
        self.object = None
        self.skus = None
        self.online_skus = None
        self.context = {}
        self.new_sku_form, self.new_offer_form  = None, None
        self.create_form_validation, self.create_offer_form_validation = None, None
        self.update_form, self.update_offer_form = None, None
        self.update_form_validation = {"pk": None, "validation": None}
        self.update_offer_form_validation = {"pk": None, "validation": None}

    def dispatch(self, request, *args, **kwargs):
        self.object = Product.objects.get(pk=self.kwargs.get("pk"))
        self.skus = self.object.sku_set.filter(main_sku=True).order_by("state")
        self.online_skus = self.get_online_skus_and_forms()

        self.new_sku_form = OnlineSkuForm()
        self.new_offer_form = OfferForm()

        if self.request.method == "POST":
            pk_from_GET = self.request.GET.get("sku_pk", "") or ""
            print(f"wie: {pk_from_GET}")
            success_redirect = HttpResponseRedirect(
                reverse_lazy("product:detail", kwargs={"pk": self.kwargs.get("pk")}))

            if pk_from_GET == "":
                self.new_sku_form = OnlineSkuForm(data=self.request.POST)
                self.new_offer_form = OfferForm(data=self.request.POST)

                self.create_form_validation = self.new_sku_form.is_valid()
                self.create_offer_form_validation = self.new_offer_form.is_valid()

                if self.create_form_validation is True and self.create_offer_form_validation is True:
                    new_sku_instance = self.create_new_sku()
                    new_offer_instance = self.create_new_offer()
                    new_offer_instance.sku_instance = new_sku_instance
                    new_offer_instance.save()
                    return success_redirect
                else:
                    return render(request, self.template_name, self.get_context())
            else:
                for sku, forms in self.online_skus.items():
                    if str(sku.pk) == pk_from_GET:
                        self.update_form = OnlineSkuForm(instance=sku, data=self.request.POST)
                        self.update_offer_form = (OfferForm(instance=sku.offer, data=self.request.POST)
                                                  if hasattr(sku, "offer") is True
                                                  else OfferForm(data=self.request.POST))
                        self.online_skus[sku]["form"] = self.update_form
                        self.online_skus[sku]["offer_form"] = self.update_offer_form
                        self.update_form_validation["validation"] = self.update_form.is_valid()
                        self.update_form_validation["pk"] = sku.pk
                        self.update_offer_form_validation["validation"] = self.update_offer_form.is_valid()
                        self.update_offer_form_validation["pk"] = sku.offer.pk if hasattr(sku, "offer") else None
                        break

                if (self.update_form_validation["validation"] is True and
                        self.update_offer_form_validation["validation"] is True):
                    sku_instance = self.update_form.save()
                    offer_instance = self.update_offer_form.save()

                    if offer_instance.pk is None:
                        offer_instance.sku_instance = sku_instance
                        offer_instance.save()
                    return success_redirect
                else:
                    return render(request, self.template_name, self.get_context())
        return super().dispatch(request, *args, **kwargs)

    def create_new_sku(self):
        print(f"??? POST")
        new_sku = self.new_sku_form.save(commit=False)
        new_sku.product = self.object
        new_sku.save()
        if new_sku.sku is None:
            new_sku.sku = new_sku.pk
            new_sku.save()
        print(f"wawawa: {new_sku.pk}")
        return new_sku

    def create_new_offer(self):
        new_offer = self.new_offer_form.save(commit=False)
        return new_offer

    def get_object(self):
        return self.object

    def get_context_data(self, **kwargs):
        self.context = super().get_context_data(**kwargs)
        self.context = self.get_context()
        return self.context

    def get_context(self):
        self.context["title"] = "Artikel Detailansicht"
        self.context["skus"] = self.skus
        self.context["online_skus"] = self.online_skus
        self.context["states_totals"], self.context["total"] = self.get_states_totals_and_total()
        self.context["form"] = self.new_sku_form
        self.context["offer_form"] = self.new_offer_form
        self.context["create_form_validation"] = self.create_form_validation
        self.context["update_form_validation"] = self.update_form_validation
        self.context["create_offer_form_validation"] = self.create_offer_form_validation
        self.context["update_offer_form_validation"] = self.update_offer_form_validation
        return self.context

    def get_online_skus_and_forms(self):
        online_skus = self.object.sku_set.filter(main_sku__isnull=True).order_by("state")
        result = {}
        for sku in online_skus:
            form = OnlineSkuForm(instance=sku)
            offer_form = OfferForm(instance=sku.offer) if hasattr(sku, "offer") is True else OfferForm()
            result[sku] = {"form": form, "offer_form": offer_form}
        return result

    def get_states_totals_and_total(self):
        states_totals, total = get_states_totals_and_total(self.object, self.object.sku_set.all())
        return states_totals, total


class OnlineSkuDeleteView(DeleteView):
    template_name = "product_sku/confirm_delete.html"

    def __init__(self):
        super().__init__()
        self.object, self.product, self.missions_products = None, None, None
        self.missions_pks, self.missions = [], None

    def dispatch(self, request, *args, **kwargs):
        self.object = Sku.objects.get(pk=self.kwargs.get("pk"), main_sku__isnull=True)
        self.product = self.object.product if self.object is not None else None
        self.missions_products = self.object.productmission_set.all()

        print(f"limaddha: {self.missions_products.count()}")
        print(f"{self.object.sku}")
        if self.missions_products.count() > 0:
            self.missions_pks = list(self.missions_products.values_list(
                "mission__pk", flat=True).order_by("mission").distinct("mission"))
            print(f"ok must work: {self.missions}")

        if request.method == "POST":

            has_picklist = None

            for mission_product in self.missions_products:
                if mission_product.picklistproducts_set.all().count() > 0:
                    has_picklist = True
                    break

            if self.object is not None and (has_picklist is True or (hasattr(self.object, "offer") is True
                                                                     and self.object.offer.amount not in [None, 0])):
                error_msg = "Diese SKU kann nicht gelöscht werden, da für diese SKU Aufträge oder Angebote bestehen."
                context = self.get_context()
                context["error_msg"] = error_msg
                return render(request, self.template_name,
                              context)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        print(f"ruffy: {self.object}")
        print(f"shank 1: {self.missions}")
        success_url = self.get_success_url()
        mission_products = ProductMission.objects.filter(sku=self.object)
        mission_products.update(no_match_sku=self.object.sku)
        self.object.delete()
        print(f"shank 2: {self.missions}")

        self.missions = Mission.objects.filter(pk__in=self.missions_pks)

        if self.missions.count() > 0:
            for mission in self.missions:
                print(f"BEFORE {mission.pk} - - - {mission.status}")
                mission.refresh_from_db()
                mission.not_matchable = True
                mission.save()
                print(f"AFTER {mission.pk} - - - {mission.status}")
        return HttpResponseRedirect(success_url)

    def get_object(self, queryset=None):
        return self.object

    def get_success_url(self):
        return reverse_lazy("product:detail", kwargs={"pk": self.product.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_context())
        return context

    def get_context(self):
        context = {"title": "Löschvorgang bestätigen", "object": self.object, "product": self.product}
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
