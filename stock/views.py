import urllib
from django.shortcuts import render, get_object_or_404
from django.views.generic import DeleteView
from django.views.generic import FormView
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django_celery_results.models import TaskResult
from import_excel.funcs import get_table_header, check_excel_for_duplicates
from mission.models import PickListProducts
from sku.models import Sku
from stock.funcs import get_records_as_list_with_dicts
from import_excel.models import TaskDuplicates
from product.models import Product, get_states_totals_and_total
from .models import Stock, Stockdocument
from stock.forms import StockdocumentForm, StockUpdateForm, ImportForm, StockCreateForm, GeneratePositionsForm, \
    GeneratePositionLevelsColumnsForm, StockCorrectForm, validate_ean_has_not_multiple_products
from tablib import Dataset
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from utils.utils import filter_queryset_from_request
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from stock.tasks import table_data_to_model_task
from erpghost import app
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from stock.models import Position, is_stock_reserved
import itertools
from rest_framework import generics
from rest_framework import serializers
from stock.models import get_states_totals_and_total_from_ean_without_product
# Create your views here.


class StockListBaseView(LoginRequiredMixin, ListView):
    paginate_by = 15
    states = Sku.objects.all().values_list("state", flat=True).distinct("state")

    def __init__(self):
        super().__init__()
        self.context = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.context)
        object_list = context["object_list"]
        context["stock_list"] = self.get_stock_list(object_list)
        context["title"] = "Lagerbestand"
        context["states"] = self.states
        return context

    def get_stock_list(self, object_list):
        result = []
        for obj in object_list:
            if obj.sku_instance is not None:
                skus = obj.sku_instance.product.sku_set.all().get_totals().order_by("state")
                states_totals, total = get_states_totals_and_total(obj.sku_instance.product, skus)
                result.append((obj, states_totals, total))
            else:
                states_totals, total = get_states_totals_and_total_from_ean_without_product(obj)
                result.append((obj, states_totals, total))
        return result

    def get_queryset(self):
        print(f"hallo:::: {self.queryset}")
        position = self.get_value_from_GET_or_session("lagerplatz", self.request)
        if position != "":
            position = position.strip()
            self.queryset = self.queryset.filter(lagerplatz__icontains=position)

        sku = self.get_value_from_GET_or_session("sku", self.request)
        if sku != "":
            sku = sku.strip()
            self.queryset = self.queryset.filter(Q(Q(sku_instance__sku__icontains=sku) | Q(sku__icontains=sku)))

        state = self.get_value_from_GET_or_session("zustand", self.request)
        if state != "":
            state = state.strip()
            self.queryset = self.queryset.filter(Q(Q(sku_instance__state=state) | Q(zustand=state)))

        title = self.get_value_from_GET_or_session("title", self.request)
        if title != "":
            title = title.strip()
            self.queryset = self.queryset.filter(Q(Q(sku_instance__product__title__icontains=title)
                                                   | Q(title__icontains=title)))

        ean = self.get_value_from_GET_or_session("ean_vollstaendig", self.request)
        if ean != "":
            ean = ean.strip()
            self.queryset = self.queryset.filter(Q(Q(sku_instance__product__ean=ean) | Q(ean_vollstaendig=ean)))

        person = self.get_value_from_GET_or_session("name", self.request)
        if person != "":
            person = person.strip()
            self.queryset = self.queryset.filter(name__icontains=person)

        q = self.get_value_from_GET_or_session("q", self.request)
        position_q = Q()
        sku_q = Q()
        state_q = Q()
        title_q = Q()
        ean_q = Q()
        person_q = Q()

        if q != "":
            q_list = q.split()
            for q_value in q_list:
                q_value = q_value.strip()
                position_q &= Q(lagerplatz__icontains=q_value)
                sku_q &= Q(Q(Q(sku_instance__sku__icontains=q_value) | Q(sku__icontains=q_value)))
                state_q &= Q(Q(sku_instance__state=q_value) | Q(zustand=q_value))
                title_q &= Q(Q(sku_instance__product__title__icontains=q_value) | Q(title__icontains=q_value))
                ean_q &= Q(Q(sku_instance__product__ean=q_value) | Q(ean_vollstaendig=q_value))
                person_q &= Q(name__icontains=q_value)

        self.queryset = self.queryset.filter(position_q | sku_q | title_q | ean_q | person_q)
        self.set_filter_and_search_values_in_context(position, sku, state, title, ean, person, q)
        print(self.context)
        return self.queryset

    def get_value_from_GET_or_session(self, name, request):
        pass

    def set_filter_and_search_values_in_context(self, position, sku, state, title, ean, person, q):
        pass


class StockListView(StockListBaseView):
    paginate_by = 15
    queryset = Stock.objects.exclude(product__single_product=True).order_by("-pk")
    states = Sku.objects.all().values_list("state", flat=True).distinct("state")

    def dispatch(self, request, *args, **kwargs):
        if self.request.GET.get("clear_filter", "") or "" == "1":
            filter_values = {"stock_lagerplatz": None, "stock_sku": None, "stock_zustand": None,
                             "stock_title": None,
                             "stock_ean_vollstaendig": None, "stock_name": None, "stock_q": None}
            for name, value in filter_values.items():
                self.request.session[name] = value
        return super().dispatch(request, *args, **kwargs)

    def set_filter_and_search_values_in_context(self, position, sku, state, title, ean, person, q):
        self.context = {"stock_lagerplatz": position, "stock_sku": sku, "stock_zustand": state, "stock_title": title,
                        "stock_ean_vollstaendig": ean, "stock_name": person, "stock_q": q}

    def get_value_from_GET_or_session(self, value, request):
        get_value = request.GET.get(value)
        if get_value is not None:
            request.session[f"stock_{value}"] = get_value.strip()
            return get_value
        else:
            if request.GET.get("q") is None:
                return request.session.get(f"stock_{value}", "") or ""
            else:
                request.session[f"stock_{value}"] = ""
                return ""


class StockListViewDEAD(LoginRequiredMixin, ListView):
    template_name = "stock/stock_list.html"
    login_url = "/login/"
    exclude_fields = ["id", "bestand", 'regal', "ean_upc", "scanner", "karton", 'box', 'aufnahme_datum',
                      "ignore_unique", "product_id"]

    def __init__(self):
        super().__init__()
        self.queryset = None

    def dispatch(self, request, *args, **kwargs):
        self.queryset = self.filter_queryset_from_request()
        self.queryset = self.set_pagination(self.queryset)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["fields"] = self.build_fields()

        # products = self.get_products()

        context["filter_fields"] = self.get_filter_fields(exclude=self.exclude_fields)

        context["search_position"] = self.get_searched_position()

        context["title"] = "Lagerbestand"
        context["filter_fields"] = self.build_filter_fields(exclude=self.exclude_fields)

        return context

    def filter_queryset_from_request(self):
        filter_dict = {}
        q_filter = Q()
        for field, verbose_name in self.get_filter_fields(exclude=["title", "product_id", "ean_vollstaendig", "sku",
                                                                   "zustand"]):
            if field in self.request.GET:
                GET_value = self.request.GET.get(field)
                if GET_value is not None and GET_value != "":
                    filter_dict[f"{field}__icontains"] = str(self.request.GET.get(field)).strip()

        print(f"OKAYYYY1 {filter_dict}")

        for item in filter_dict:
            q_filter &= Q(**{item: filter_dict[item]})

        sku_filter = Q()

        if self.request.GET.get("sku") is not None and self.request.GET.get("sku") != "":
            sku = self.request.GET.get("sku").strip()

            sku_q_filter = Q(sku__iexact=sku)

            ean_state_filter = Q()

            if self.request.GET.get("zustand") is not None and self.request.GET.get("zustand") != "":
                zustand = self.request.GET.get("zustand").strip()
                skus = Sku.objects.filter(sku__iexact=sku, state=zustand)

                if skus.count() == 0:
                    sku_q_filter = Q(sku__iexact=sku, zustand=zustand)  # DAMIT ER FAILT !
            else:
                skus = Sku.objects.filter(sku__iexact=sku)

            for sku in skus:
                sku_ean = sku.product.ean
                sku_state = sku.state

                if sku_ean != "" and sku_ean is not None:
                    ean_state_filter |= Q(ean_vollstaendig=sku_ean, zustand=sku_state)
            sku_filter &= Q(sku_q_filter | ean_state_filter)

        ean_title_q_filter = Q()

        if self.request.GET.get("title") is not None and self.request.GET.get("title") != "":
            title = self.request.GET.get("title").strip()
            if self.request.GET.get("zustand") is not None and self.request.GET.get("zustand") != "":
                zustand = self.request.GET.get("zustand")
                skus = Sku.objects.filter(state=zustand, product__title__icontains=title).values("sku")
                skus_list = [sku.get("sku") for sku in skus]
                ean_title_q_filter &=\
                    Q(product__title__icontains=title, zustand=zustand) |\
                    Q(title__icontains=title, zustand=zustand) | Q(sku__in=skus_list)
            else:
                ean_title_q_filter &= Q(product__title__icontains=title) | Q(title__icontains=title)

        if self.request.GET.get("ean_vollstaendig") is not None and self.request.GET.get("ean_vollstaendig") != "":
            ean_vollstaendig = self.request.GET.get("ean_vollstaendig").strip()
            if self.request.GET.get("zustand") is not None and self.request.GET.get("zustand") != "":
                zustand = self.request.GET.get("zustand")
                skus = Sku.objects.filter(state=zustand, product__ean__icontains=ean_vollstaendig).values("sku")
                skus_list = [sku.get("sku") for sku in skus]

                ean_title_q_filter &= \
                    Q(
                        Q(ean_vollstaendig__icontains=ean_vollstaendig, zustand=zustand)
                        | Q(sku__in=skus_list)
                    )
            else:
                ean_title_q_filter &= \
                    Q(product__ean__icontains=ean_vollstaendig) | Q(ean_vollstaendig__icontains=ean_vollstaendig)

        if (self.request.GET.get("title") is None or self.request.GET.get("title") == "") and\
                (self.request.GET.get("ean_vollstaendig") is None or self.request.GET.get("ean_vollstaendig") == "")\
                and (self.request.GET.get("sku") is None or self.request.GET.get("sku") == ""):
            if self.request.GET.get("zustand") is not None and self.request.GET.get("zustand") != "":
                zustand = self.request.GET.get("zustand")
                skus = Sku.objects.filter(state=zustand).values("sku")
                print(skus)
                skus_list = [sku.get("sku") for sku in skus]
                print(skus_list)
                q_filter &= Q(zustand=zustand) | Q(sku__in=skus_list)

        q_filter &= ean_title_q_filter

        q_filter &= sku_filter

        print(q_filter)
        queryset = Stock.objects.filter(q_filter).order_by("-id")
        return queryset

    def get_products_states(self, products, stocks):
        products_states = []
        for product, stock in zip(products, stocks):
            if product is not None and product != "":
                print(stock)
                products_states.append(product.get_state_from_sku(stock.sku))
            else:
                products_states.append(None)
        return products_states

    def get_product_stocks(self):
        queryset = self.get_queryset()
        total_stocks = []
        for q in queryset:
            stock_dict = {}
            stock = None
            product = None

            if q.ean_vollstaendig is not None and q.ean_vollstaendig != "":
                stock = Stock.objects.filter(ean_vollstaendig=q.ean_vollstaendig).first()
                product = Product.objects.filter(ean=q.ean_vollstaendig).first()

            if q.sku is not None and q.sku != "":
                stock = Stock.objects.filter(sku=q.sku).first()
                product = Product.objects.filter(sku__sku=q.sku).first()

            if q.title is not None and q.title != "":
                stock = Stock.objects.filter(title=q.title).first()

            if stock is not None:
                total = stock.get_available_stocks_of_total_stocks(product=product)

                stock_dict["total"] = total.get("Gesamt")
                stock_dict["total_neu"] = total.get("Neu")
                stock_dict["total_g"] = total.get("G")
                stock_dict["total_b"] = total.get("B")
                stock_dict["total_c"] = total.get("C")
                stock_dict["total_d"] = total.get("D")

                total_stocks.append(stock_dict)
            else:
                stock_dict["total"] = None
                total_stocks.append(stock_dict)
        return total_stocks

    def get_searched_position(self):
        GET_value = self.request.GET.get("lagerplatz", "").strip()
        if GET_value is not None and GET_value != "":
            position_from_GET_request = self.request.GET.get("lagerplatz").strip()
            return filter_queryset_from_position_string(position_from_GET_request, Position).first()

    def build_filter_fields(self, exclude=list):
        filter_fields = []
        for field in Stock._meta.get_fields():
            if hasattr(field, "attname") is False or field.attname in exclude:
                continue
            value = self.request.GET.get(field.attname, "").strip()
            filter_fields.append((field.attname, field.verbose_name, value))
        return filter_fields

    def build_fields(self):
        fields = self.get_verbose_names(exclude=["id", "ean_upc", "scanner", "name", "karton", "box",
                                                 "aufnahme_datum", "ignore_unique", "regal", "product_id",
                                                 "missing_amount"])
        fields.append("Gesamt Bestand")
        fields = ["", "Bild"] + fields
        return fields

    def get_products(self):
        queryset = self.get_queryset()
        products = []
        for q in queryset:
            product = None

            if q.ean_vollstaendig is not None and q.ean_vollstaendig != "":

                product = Product.objects.filter(ean=q.ean_vollstaendig).first()

            else:
                if q.sku is not None and q.sku != "":
                    product = Product.objects.filter(sku__sku=q.sku).first()

            if product is not None:
                products.append(product)
            else:
                products.append(None)
        return products

    def set_pagination(self, queryset):
        page = self.request.GET.get("page")
        paginator = Paginator(queryset, 15)
        if not page:
            page = 1
        current_page_object = paginator.page(int(page))
        return current_page_object

    def get_verbose_names(self, exclude=None):
        fields = Stock._meta.get_fields()
        verbose_fields = []
        for field in fields:
            if hasattr(field, "verbose_name") is False:
                continue
            if field.attname not in exclude:
                verbose_fields.append(field.verbose_name)
        return verbose_fields

    def get_filter_fields(self, exclude=None):
        filter_fields = []
        fields = Stock._meta.get_fields()
        for field in fields:
            if hasattr(field, "verbose_name") is False:
                continue
            if field.attname not in exclude:
                filter_fields.append((field.attname, field.verbose_name))
        return filter_fields


class StockDocumentDetailView(LoginRequiredMixin, DetailView):
    template_name = "stock/stock_document_detail.html"

    def get_object(self):
        obj = get_object_or_404(Stockdocument, pk=self.kwargs.get("pk"))
        return obj


class StockDetailView(LoginRequiredMixin, DetailView):
    template_name = "stock/stock_detail.html"

    def __init__(self):
        super().__init__()
        self.object = None
        self.position = None

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Stock, pk=self.kwargs.get("pk"))
        if self.object is not None:
            print(f"wie: {self.object.lagerplatz}")
            self.position = Position.objects.filter(name__iexact=self.object.lagerplatz).first()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.object

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = f"Inventar {context.get('object').lagerplatz}"
        context["product"] = self.get_product()
        context["position"] = self.position
        context["sku_state"] = self.get_sku_state()
        context["states_totals"], context["total"] = self.get_states_totals_and_total()
        return context

    def get_states_totals_and_total(self):
        if self.object.sku_instance is not None:
            skus = self.object.sku_instance.product.sku_set.all().get_totals().order_by("state")
            states_totals, total = get_states_totals_and_total(self.object.sku_instance.product, skus)
            return states_totals, total
        else:
            return None, None

    def get_sku_state(self):
        product = self.object.get_product()
        if product is not None:
            return product.get_state_from_sku(self.object.sku)

    def get_product(self):
        product = None
        if self.object.ean_vollstaendig is not None and self.object.ean_vollstaendig != "":
            product = Product.objects.filter(ean=self.object.ean_vollstaendig).first()
        else:
            if self.object.sku is not None and self.object.sku != "":
                product = Product.objects.filter(sku__sku=self.object.sku).first()
        return product

    def get_product_stocks(self):
        query = self.get_object()
        stock = None
        stock_dict = {}

        if query.ean_vollstaendig is not None and query.ean_vollstaendig != "":
            stock = Stock.objects.filter(ean_vollstaendig=query.ean_vollstaendig).first()

        if query.sku is not None and query.sku != "":
            stock = Stock.objects.filter(sku=query.sku).first()

        if query.title is not None and query.title != "":
            stock = Stock.objects.filter(title=query.title).first()

        if stock is not None:
            total = stock.get_available_stocks_of_total_stocks()

            stock_dict["total"] = total.get('Gesamt')
            stock_dict["total_neu"] = total.get("Neu")
            stock_dict["total_g"] = total.get("G")
            stock_dict["total_b"] = total.get("B")
            stock_dict["total_c"] = total.get("C")
            stock_dict["total_d"] = total.get("D")
        return stock_dict


class StockUpdateBaseView(LoginRequiredMixin, UpdateView):
    template_name = "stock/form.html"
    login_url = "/login/"

    def __init__(self):
        super().__init__()
        self.object = None
        self.instance = None
        self.position = None

    def get_object(self):
        print(f"wa: {self.object.pk}")
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["instance"] = self.instance
        context["position"] = self.position
        if not self.request.POST:
            context["object"] = self.get_object()
        context["title"] = "Inventar bearbeiten"
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)

        if self.object.pk is not None:
            print(f"ben ben: {self.object.pk}")

            state = self.object.get_state()

            if (state, state) not in form.fields["zustand"].choices:
                choices_with_object_zustand_value = form.fields["zustand"].choices
                form.fields["zustand"].choices.append((state, state))
                form.fields["zustand"]._set_choices(choices_with_object_zustand_value)
        return form

    def get_product(self, form):
        product = None
        ean = form.data.get("ean_vollstaendig", "") or ""
        ean = ean.strip()
        sku = form.data.get("sku", "") or ""
        sku = sku.strip()
        if sku is not None and sku != "":
            product = Product.objects.filter(sku__sku=sku).first()

        if ean is not None and ean != "":
            product = Product.objects.filter(ean=ean).first()

        print(f"INWI: {ean} - {sku} - {product}")
        return product


class StockUpdateView(StockUpdateBaseView):
    form_class = StockUpdateForm

    def dispatch(self, request, *args, **kwargs):
        self.object = Stock.objects.get(id=self.kwargs.get("pk"))

        if self.object is not None:
            self.position = Position.objects.filter(name__iexact=self.object.lagerplatz).first()
        self.instance = Stock.objects.get(id=self.kwargs.get("pk"))
        print(f"hää: {self.instance.sku_instance.product.single_product}")
        if (self.instance.sku_instance is not None and self.instance.sku_instance.product is not None and
                self.instance.sku_instance.product.single_product is True):
            return HttpResponseRedirect(reverse_lazy("stock:single_edit", kwargs={"pk": self.instance.pk}))
        return super().dispatch(request, *args, **kwargs)


class StockDeleteQuerySetView(DeleteView):
    model = Stock
    success_url = reverse_lazy("stock:list")
    template_name = "stock/confirm_delete.html"

    def __init__(self):
        super().__init__()
        self.context = {}
        self.exclude_stocks = None

    def get_context_data(self, **kwargs):
        self.context = super().get_context_data(**kwargs)
        self.context["title"] = "Bestände ausbuchen"
        self.context["exclude_stocks"] = self.exclude_stocks
        return self.context

    def get_object(self, queryset=None):
        # die excluden die reserviert sind
        # die excludeten auch nochmal anzeigen in View
        exclude_stocks = []
        stocks = Stock.objects.filter(id__in=self.request.GET.getlist('item'))
        for stock in stocks:
            skus = (stock.sku_instance.product.sku_set.all()
                    if stock.sku_instance is not None and stock.sku_instance.product is not None
                    else stock.zustand or "")
            state = (stock.sku_instance.state if stock.sku_instance is not None else stock.zustand or "")
            states_totals, total = get_states_totals_and_total(stock.sku_instance.product, skus)
            print(f"hehe: {states_totals[state]}")

            reserved_amount_position = PickListProducts.objects.get_stock_reserved_total(stock).get("total", 0) or 0

            print(f" WHAT THE: {reserved_amount_position}")

            available_total = states_totals[state].get("available_total", "") or 0
            if available_total - int(stock.bestand) < 0 or reserved_amount_position > 0:
                print(f"Der Artikel kann maximal {available_total} ausgebucht werden.")
                exclude_stocks.append((stock, available_total, reserved_amount_position))

        stocks = stocks.exclude(id__in=[stock.pk for stock, _, _ in exclude_stocks])
        self.exclude_stocks = exclude_stocks
        return stocks


class StockDeleteView(DeleteView):
    model = Stock
    success_url = reverse_lazy("stock:list")

    def __init__(self):
        self.object = None
        super().__init__()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object = context["object"]
        product_ean_or_sku_or_title = self.get_product_ean_or_sku_or_title(self.object)
        context["product_ean_or_sku_or_title"] = product_ean_or_sku_or_title
        context['title'] = f"{self.object.bestand} x Artikel {product_ean_or_sku_or_title} von " \
                           f"{self.object.lagerplatz} ausbuchen"
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        print(self.object)
        reserved_stock = is_stock_reserved(self.object)
        print(f"babababa: {reserved_stock}")

        if reserved_stock > 0:
            context["error"] = f"Auf diesen Lagerplatz ist der Artikel {reserved_stock}x reserviert."
            return render(request, "stock/stock_confirm_delete.html", context)

        state = self.object.zustand
        if state is None or state == "":
            sku = Sku.objects.filter(sku__iexact=self.object.sku).first()
            if sku is not None and sku != "":
                state = sku.state

        if state is not None and state != "":
            reserved_stock = self.object.get_reserved_stocks().get(state)
            available_stock = self.object.get_available_total_stocks().get(state)

            if reserved_stock > 0:
                if int(self.object.bestand) > int(available_stock):

                    if int(available_stock) <= 0:
                        context["error"] = f"Sie können diesen Bestand nicht ausbuchen. \n" \
                                           f"Der gesamte Bestand von diesem Artikel ist reserviert."
                    else:
                        context["error"] = f"Sie können diesen Bestand nicht ausbuchen.\n Sie können maximal " \
                                           f"{int(available_stock)} stk von diesem Artikel ausbuchen."
                    return render(request, "stock/stock_confirm_delete.html", context)

        messages.add_message(self.request, messages.INFO, "Artikel wurde erfolgreich ausgebucht")
        return super().delete(request, *args, **kwargs)

    def get_product_ean_or_sku_or_title(self, obj):
        if obj.ean_vollstaendig is not None and obj.ean_vollstaendig != "":
            return obj.ean_vollstaendig
        elif obj.sku is not None and obj.sku != "":
            return obj.sku
        elif obj.title is not None and obj.title != "":
            return obj.title


class StockCorrectView(UpdateView):
    template_name = "stock/stock_correct_form.html"
    form_class = StockCorrectForm

    def __init__(self):
        super().__init__()
        self.object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = Stock.objects.get(pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lagerbestand korrigieren"
        context["object"] = self.object
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if int(self.object.bestand) == 0:
            self.object.delete()
            messages.add_message(self.request, messages.INFO, "Artikel wurde erfolgreich ausgebucht")
            return HttpResponseRedirect(reverse_lazy("stock:list"))
        return super().form_valid(form)


class StockImportView(FormView):
    template_name = "stock/import.html"
    form_class = ImportForm
    success_url = reverse_lazy("stock:import")

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["title"] = "Lagerbestand Import"
        context["tasks_results"] = TaskResult.objects.all().order_by("-id")[:10]
        recent_task_duplicates_queryset = TaskDuplicates.objects.filter(
            task_id=context["tasks_results"].first().task_id)

        recent_duplicates = []
        for duplicate in recent_task_duplicates_queryset:
            query_dict = urllib.parse.parse_qs(duplicate.query_string)
            query_dict = {k: v[0] for k, v in query_dict.items()}
            recent_duplicates.append(query_dict)
        context["recent_duplicates"] = recent_duplicates

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

        header = get_table_header(file_type, content)

        excel_header_fields = ["ean_vollstaendig", "lagerplatz", "zustand", "bestand", "regal", "scanner",
                               "name", "karton", "box", "aufnahme_datum"]

        excel_list = get_records_as_list_with_dicts(file_type, content, header, excel_header_fields)

        excel_duplicates = check_excel_for_duplicates(excel_list)

        if excel_duplicates:
            context = self.get_context_data(**kwargs)
            context["excel_duplicates"] = excel_duplicates
            return render(self.request, self.template_name, context)

        unique_together = ["ean_vollstaendig", "lagerplatz", "zustand"]

        table_data_to_model_task.delay(excel_list, ("stock", "Stock"), unique_together)
        return super().post(request, *args, **kwargs)


class PositionListView(LoginRequiredMixin, ListView):
    template_name = "stock/position/position_list.html"
    exclude_fields = ["id"]

    def get_queryset(self):
        queryset = self.filter_model_from_get_request(Position)
        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lagerpositionen"
        context["fields"] = self.build_header_fields(exclude=self.exclude_fields)
        context["filter_fields"] = self.build_filter_fields()
        return context

    def build_filter_fields(self):
        filter_fields = []
        position = self.request.GET.get("position", "") or ""
        position = position.strip()
        filter_fields.append(("position", "Lagerplatz", position))
        return filter_fields

    def build_header_fields(self, exclude=list):
        fields = ["", "Position"]
        for field in Position._meta.get_fields():
            if field.attname in exclude:
                continue
            fields.append(field.verbose_name)
        fields.append("")
        return fields

    def filter_model_from_get_request(self, model_class):
        position = self.request.GET.get("position", "") or ""
        position = position.strip()
        return filter_queryset_from_position_string(position, model_class)

    def set_pagination(self, queryset):
        current_page = self.request.GET.get("page")
        if current_page is None:
            current_page = 1
        return Paginator(queryset, 15).page(current_page)


def filter_queryset_from_position_string(GET_value, model_class):
    if GET_value == "" or GET_value is None:
        return model_class.objects.all()
    match_ids = []
    for p in model_class.objects.all():
        position = p.position
        if GET_value.lower() in position.lower():
            match_ids.append(p.id)
    return model_class.objects.filter(id__in=match_ids)


class NoneSingleStockCreateForm(StockCreateForm):
    def clean(self):
        super().clean()
        sku = self.cleaned_data.get("sku", "") or ""
        sku = sku.strip()
        if sku != "":
            sku_instance = Sku.objects.filter(sku__iexact=sku).first()
            if sku_instance is not None:
                product = sku_instance.product
                if product is not None:
                    if product.single_product is True:
                        self.add_error(None, "<h3 style='color:red;'>Die angegebene SKU ist ein Einzelartikel</h3>"
                                             "<p style='color:red;'>Sie können diesen Artikel im Einzelhandel buchen"
                                             "</p>")
        return self.cleaned_data


class BookProductToPositionView(LoginRequiredMixin, CreateView):
    template_name = "stock/form.html"
    form_class = NoneSingleStockCreateForm
    login_url = "/login/"

    def __init__(self):
        super().__init__()
        self.current_position = None
        self.object = None

    def dispatch(self, request, *args, **kwargs):
        self.current_position = Position.objects.filter(pk=self.kwargs.get("pk")).first()
        self.current_position = self.current_position.name if self.current_position is not None else None
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Artikel zu Position buchen'
        context["object"] = Stock(lagerplatz=self.current_position)
        return context

    def get_initial(self):
        return {
            'lagerplatz': self.current_position,
        }

    def form_valid(self, form):
        self.object = form.save(commit=False)
        product = self.get_product(form)

        if product is not None:
            print(f"before gate: {product.single_product}")
            if product.single_product is None or product.single_product == "":
                ean = (self.object.ean_vollstaendig or "").strip()
                state = (self.object.zustand or "").strip()

                validate_ean_has_not_multiple_products(ean, state, form)

            if product.single_product is not None and product.single_product != "":
                stock = Stock.objects.filter(sku_instance__product=product, sku_instance__product__single_product=True)

                print(f"wie {stock.count()}")
                if stock.count() > 0:
                    stock = stock.first()

                    stock_has_sku_instance_and_product = (stock.sku_instance is not None
                                                          and stock.sku_instance.product is not None)

                    sku = (stock.sku_instance.sku if stock_has_sku_instance_and_product
                           else self.object.sku or "").strip()

                    ean = (stock.sku_instance.product.ean if stock_has_sku_instance_and_product else '').strip()

                    state = (stock.sku_instance.state if stock_has_sku_instance_and_product
                             else self.object.zustand or "").strip()

                    title = (stock.product.title if stock_has_sku_instance_and_product else stock.title or '').strip()

                    img_tag = ""

                    if (stock_has_sku_instance_and_product and stock.sku_instance.product.main_image is not None
                            and stock.sku_instance.product.main_image != ""):
                        img_tag = f"<img src='{stock.sku_instance.product.main_image.url}' class='img-responsive'" \
                                  f" style='max-height:80px;'/>"

                    form.add_error(None, f"<h3 style='color:red;'>Dieser Artikel ist bereits eingebucht</h3>"
                                         f"<p style='color:red;' class='help-block'>"
                                         f"Einzelartikel können nur einmal auf einer Lagerposition eingebucht werden"
                                         f"</p>"
                                         f"<p><table class='table table-bordered'>"
                                         f"<tr><th></th><th>Bild</th><th>EAN</th><th>SKU</th>"
                                         f"<th>Zustand</th><th>Artikelname</th>"
                                         f"<th>Lagerplatz</th></tr><tr><td><p><a href="
                                         f"'{reverse_lazy('stock:detail', kwargs={'pk': stock.pk})}'>"
                                         f"Ansicht</a></p><a href="
                                         f"'{reverse_lazy('stock:edit', kwargs={'pk': stock.pk})}'>Bearbeiten</a><p>"
                                         f"</p></td>"
                                         f"<td>{img_tag}</td><td>{ean}</td>"
                                         f"<td>{sku}</td><td>{ state }</td>"
                                         f"<td>{title}</td>"
                                         f"<td>{stock.lagerplatz}</td><tr/></table>")
                bestand = self.object.bestand
                if bestand is not None and bestand != "":
                    if int(bestand) > 1:
                        form.add_error("bestand", f"Der Bestand darf nicht größer als 1 sein, da "
                                                  f"der Artikel ein Einzelartikel ist.")

        if form.is_valid() is False:
            return super().form_invalid(form)

        if self.current_position is not None:
            self.object.lagerplatz = self.current_position

        return super().form_valid(form)

    def get_product(self, form):
        product = None

        ean = form.cleaned_data.get("ean_vollstaendig", "") or ""
        ean = ean.strip()
        sku = form.data.get("sku", "") or ""
        sku = sku.strip()

        if sku is not None and sku != "":
            product = Product.objects.filter(sku__sku=sku).first()
        print(f"warum: {product}")
        if ean is not None and ean != "":
            product = Product.objects.filter(ean=ean, single_product__isnull=True).first()

        print(f"INWI: {ean} - {sku} - {product.pk}")
        return product


class GeneratePositionsView(FormView):
    template_name = "stock/position/generate_positions.html"
    form_class = GeneratePositionsForm
    success_url = reverse_lazy("stock:position_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lagerpositionen generieren"
        context["level_position_forms"] = [GeneratePositionLevelsColumnsForm()]
        return context

    def form_valid(self, form):
        context = self.get_context_data()

        amount_rows = len(self.request.POST.getlist("level"))

        level_position_forms_list = []

        column_from_to_list = []

        bulk_instances = []
        shelf_number = form.cleaned_data.get("shelf_number")
        prefix = form.cleaned_data.get("prefix")

        for row_count in range(0, amount_rows):
            data = {"level": self.request.POST.getlist("level")[row_count],
                    "columns_from": self.request.POST.getlist("columns_from")[row_count],
                    "columns_to": self.request.POST.getlist("columns_to")[row_count]
                    }

            column_from_to_list.append((data.get("level"), data.get("columns_from"), data.get("columns_to")))

            level_position_form = GeneratePositionLevelsColumnsForm(data=data)

            level_position_forms_list.append(level_position_form)

            print(level_position_form.data)

            if level_position_form.is_valid():

                level = int(level_position_form.cleaned_data.get("level"))
                columns_from = int(level_position_form.cleaned_data.get("columns_from"))
                columns_to = int(level_position_form.cleaned_data.get("columns_to"))

                levels = [level]
                columns = [col for col in range(columns_from, columns_to+1)]

                cartesian = [levels, columns]

                for element in itertools.product(*cartesian):
                    level = str(element[0])
                    column = str(element[1])
                    p = Position(prefix=prefix, shelf=shelf_number, level=level, column=column)
                    print(p.position)
                    bulk_instances.append(p)

        context["level_position_forms"] = level_position_forms_list

        for level_position_form in level_position_forms_list:
            if level_position_form.is_valid() is False:
                return render(self.request, self.template_name, context)

        if self.validate_positions_have_no_duplicates_in_model(bulk_instances, context) is False:
            return render(self.request, self.template_name, context)

        if self.validate_forms_level_has_no_duplicates(level_position_forms_list, context) is False:
            return render(self.request, self.template_name, context)

        if self.validate_column_from_is_less_than_column_to(column_from_to_list, context) is False:
            return render(self.request, self.template_name, context)

        Position.objects.bulk_create(bulk_instances)
        return super().form_valid(form)

    def validate_column_from_is_less_than_column_to(self, column_from_to_list, context):
        html_error_msg = f"<h4 style='color:red;'>'Plätze von' darf nicht größer als 'Plätze bis' sein:<br/><br/>" \
                         f"<ul>"
        has_column_from_greater_than_column_to = False
        for level, column_from, column_to in column_from_to_list:
            if int(column_from) > int(column_to):
                has_column_from_greater_than_column_to = True
                html_error_msg += f"<li><b>{column_from}</b> bis <b>{column_to}</b> auf Ebene <b>{level}</b></li>"
        html_error_msg += "</ul></h4>"
        if has_column_from_greater_than_column_to is True:
            context["column_from_greater_column_to_errors"] = html_error_msg
            return False
        else:
            return True

    def validate_forms_level_has_no_duplicates(self, level_position_forms_list, context):
        levels = []
        for level_position_form in level_position_forms_list:
            cleaned_data = level_position_form.cleaned_data
            levels.append(cleaned_data.get("level"))

        duplicates = []
        if len(set(levels)) != len(levels):
            print(set(levels))
            for i, level in enumerate(levels):
                for next_, level_next in enumerate(levels):
                    if next_ != i:
                        if level == level_next:
                            duplicates.append(level)
                        print(f"{i} -- {level} --- {next_} .. {level_next}")
            print(set(duplicates))
            duplicates_msg = f"<h4 style='color:red;'>Folgende Ebenen sind doppelt eingetragen: " \
                             f"<span style='color:black;'>"
            for duplicate in set(duplicates):
                duplicates_msg += f"{duplicate}, "
            duplicates_msg = duplicates_msg[:-1]
            duplicates_msg = duplicates_msg[:-1]

            duplicates_msg += f"</span></h4>"
            context["duplicate_levels"] = duplicates_msg
            print(duplicates_msg)
            return False
        else:
            return True

    def validate_positions_have_no_duplicates_in_model(self, positions, context):
        has_duplicates = False
        duplicates_html = f"<div class='col-md-12'>" \
                          f"<h3 style='color:red;'>Folgende Positionen sind bereits vorhanden</h3>" \
                          f"<table class='table table-bordered'>" \
                          f"<thead><tr><th>Position</th></tr></thead>" \
                          f"<tbody>"
        for position in positions:
            position_queryset = Position.objects.filter(prefix=position.prefix, shelf=position.shelf, level=position.level,
                                                        column=position.column)
            print(f"WHAT? {position_queryset.count()}")

            if position_queryset.count() >= 1:
                has_duplicates = True
                duplicates_html += f"<tr><td>{position.position}</td></tr>"

        duplicates_html += f"</tbody></table></div>"

        if has_duplicates is True:
            context["error_duplicates"] = duplicates_html
            return False
        else:
            return True


class PositionDeleteView(DeleteView):
    model = Position
    success_url = reverse_lazy("stock:position_list")
    template_name = "stock/position/position_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lagerplätze löschen"
        return context

    def get_object(self, queryset=None):
        return Position.objects.filter(id__in=self.request.GET.getlist('item'))


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["position"]


class PositionListAPIView(generics.ListAPIView):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer

    def get_queryset(self):
        """ allow rest api to filter by submissions """
        queryset = Position.objects.all()
        prefix = self.request.query_params.get('prefix', None)
        shelf = self.request.query_params.get('shelf', None)
        level = self.request.query_params.get('level', None)

        if prefix is not None:
            queryset = queryset.filter(prefix=prefix)
        if shelf is not None:
            queryset = queryset.filter(shelf=shelf)
        if level is not None:
            queryset = queryset.filter(level=level)

        return queryset