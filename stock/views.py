import urllib
from django.shortcuts import render, get_object_or_404
from django.views.generic import DeleteView
from django.views.generic import FormView
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django_celery_results.models import TaskResult
from import_excel.funcs import get_table_header, check_excel_for_duplicates
from stock.funcs import get_records_as_list_with_dicts
from import_excel.models import TaskDuplicates
from product.models import Product
from .models import Stock, Stockdocument
from stock.forms import StockdocumentForm, StockUpdateForm, ImportForm, StockCreateForm, GeneratePositionsForm, \
    GeneratePositionLevelsColumnsForm
from tablib import Dataset
from .resources import StockResource
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from utils.utils import filter_queryset_from_request
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from stock.tasks import table_data_to_model_task
from erpghost import app
from django.core.paginator import Paginator
from django.db.models import Q
from stock.models import Position
import itertools


# Create your views here.


class StockListView(LoginRequiredMixin, ListView):
    template_name = "stock/stock_list.html"
    login_url = "/login/"
    exclude_fields = ["id", "bestand", 'regal', "ean_upc", "scanner", "karton", 'box', 'aufnahme_datum',
                      "ignore_unique"]

    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Stock).order_by("-id")
        return self.set_pagination(queryset)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context["fields"] = self.build_fields()

        context["object_list"] = self.get_queryset()

        products = self.get_products()

        product_stocks = self.get_product_stocks()

        context["object_list_zip"] = zip(context["object_list"], products, product_stocks)

        context["filter_fields"] = self.get_filter_fields(exclude=self.exclude_fields)

        context["search_position"] = self.get_searched_position()

        context["title"] = "Lagerbestand"
        context["filter_fields"] = self.build_filter_fields(exclude=self.exclude_fields)

        return context

    def get_product_stocks(self):
        queryset = self.get_queryset()
        total_stocks = []
        for q in queryset:
            stock_dict = {}
            stock = None

            if q.ean_vollstaendig is not None and q.ean_vollstaendig != "":
                stock = Stock.objects.filter(ean_vollstaendig=q.ean_vollstaendig).first()

            if q.sku is not None and q.sku != "":
                stock = Stock.objects.filter(sku=q.sku).first()

            if q.title is not None and q.title != "":
                stock = Stock.objects.filter(title=q.title).first()

            if stock is not None:
                total = stock.get_available_stocks_of_total_stocks()

                stock_dict["total"] = total.get("Gesamt")
                stock_dict["total_neu"] = total.get("Neu")
                stock_dict["total_a"] = total.get("A")
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
            if field.attname in exclude:
                continue
            value = self.request.GET.get(field.attname, "").strip()
            filter_fields.append((field.attname, field.verbose_name, value))
        return filter_fields

    def build_fields(self):
        fields = self.get_verbose_names(exclude=["id", "ean_upc", "scanner", "name", "karton", "box",
                                                 "aufnahme_datum", "ignore_unique", "regal"])
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


class StockCreateView(LoginRequiredMixin, CreateView):
    template_name = "stock/stock_create.html"
    form_class = StockdocumentForm
    login_url = "/login/"

    def form_valid(self, form, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        stock_resource = StockResource()
        dataset = Dataset()
        document = form.cleaned_data["document"]

        imported_data = dataset.load(document.read())
        dataset.insert_col(0, lambda r: "", header='id')

        is_only_block = has_only_block(imported_data)

        if is_only_block is False:
            duplicate = check_duplicate_inside_excel(imported_data)

            if duplicate:
                error_messages = ['Doppelter Eintrag in <b>Exceldatei</b>!', duplicate]
                return render_error_page(self, context, form, error_messages)

            for row in imported_data:
                if Stock.objects.filter(lagerplatz=row[4], ean_vollstaendig=row[1], zustand=row[6]).exists():
                    error_messages = ['Eintrag in <b>Datenbank</b> vorhanden!', f"{row[1]} - {row[4]} - {row[6]} "]
                    return render_error_page(self, context, form, error_messages)

        result = stock_resource.import_data(dataset, dry_run=True)  # Test the data import
        if not result.has_errors():
            stock_resource.import_data(dataset, dry_run=False)  # Actually import
        else:
            error_messages = ["Ein unbekannter Fehler ist aufgetaucht!"]
            return render_error_page(self, context, form, error_messages)
        messages.success(self.request, f"{document} erfolgreich hochgeladen!")
        super(StockCreateView, self).form_valid(form)
        return HttpResponseRedirect(self.get_success_url())


def render_error_page(self_, context, form, error_messages):
    for error_message in error_messages:
        messages.error(self_.request, error_message)
    super(StockCreateView, self_).form_valid(form)
    return render(self_.request, self_.template_name, context)


def has_only_block(arr):
    for i, row in enumerate(arr):
        if "block" not in row[4].lower():
            return False
    return True


def check_duplicate_inside_excel(arr):
    for i, row in enumerate(arr):
        for j, against_row in enumerate(arr):
            if i != j:
                if row[1] == against_row[1] and row[4] == against_row[4] and row[6] == against_row[6]:
                    print(f"error: {row[1]} - {row[4]} - {row[6]} " \
                          f"== {against_row[1]} - {against_row[4]} - {against_row[6]}")
                    return f"{row[1]} - {row[4]} - {row[6]} " \
                           f"== {against_row[1]} - {against_row[4]} - {against_row[6]}"


class StockDocumentDetailView(LoginRequiredMixin, DetailView):
    template_name = "stock/stock_document_detail.html"

    def get_object(self):
        obj = get_object_or_404(Stockdocument, pk=self.kwargs.get("pk"))
        return obj


class StockDetailView(LoginRequiredMixin, DetailView):
    template_name = "stock/stock_detail.html"

    def get_object(self):
        obj = get_object_or_404(Stock, pk=self.kwargs.get("pk"))
        return obj

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = f"Inventar {context.get('object').lagerplatz}"
        context["product"] = self.get_product()
        context["stock"] = self.get_product_stocks()
        return context

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
            stock_dict["total_a"] = total.get("A")
            stock_dict["total_b"] = total.get("B")
            stock_dict["total_c"] = total.get("C")
            stock_dict["total_d"] = total.get("D")
        return stock_dict


class StockUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "stock/form.html"
    form_class = StockUpdateForm
    login_url = "/login/"

    def get_object(self):
        object = Stock.objects.get(id=self.kwargs.get("pk"))
        return object

    def get_context_data(self, *args, **kwargs):
        context = super(StockUpdateView, self).get_context_data(*args, **kwargs)

        if not self.request.POST:
            context["object"] = self.get_object(*args, **kwargs)
            context["title"] = "Inventar bearbeiten"
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        choices_with_object_zustand_value = form.fields["zustand"].choices
        for k, v in choices_with_object_zustand_value:
            print(f"{k} - {self.object.zustand} --- {v} --- {self.object.zustand}")
            if k == self.object.zustand or v == self.object.zustand:
                return form
        form.fields["zustand"].choices.append((self.object.zustand, self.object.zustand))
        form.fields["zustand"]._set_choices(choices_with_object_zustand_value)
        return form


class StockDeleteView(DeleteView):
    model = Stock
    success_url = reverse_lazy("stock:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context["object"]
        product_ean_or_sku_or_title = self.get_product_ean_or_sku_or_title(obj)
        context["product_ean_or_sku_or_title"] = product_ean_or_sku_or_title
        context['title'] = f"{obj.bestand} x Artikel {product_ean_or_sku_or_title} von {obj.lagerplatz} ausbuchen"
        return context

    def delete(self, request, *args, **kwargs):
        messages.add_message(self.request, messages.INFO, "Artikel wurde erfolgreich ausgebucht")
        return super().delete(request, *args, **kwargs)

    def get_product_ean_or_sku_or_title(self, obj):
        if obj.ean_vollstaendig is not None and obj.ean_vollstaendig != "":
            return obj.ean_vollstaendig
        elif obj.sku is not None and obj.sku != "":
            return obj.sku
        elif obj.title is not None and obj.title != "":
            return obj.title


class StockCopyView(StockUpdateView):
    def get_object(self):
        position = Stock.objects.get(pk=self.kwargs.get("pk")).lagerplatz
        copy = Stock()
        copy.lagerplatz = position
        copy.zustand = "Neu"
        return copy

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = f"Neuen Artikel zu Position {self.object.lagerplatz} buchen"
        return context

    def form_valid(self, form, *args, **kwargs):
        self.object.id = Stock.objects.latest("id").id+1
        self.object.save()
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
        context["title"] = "Lagerplätze"
        context["fields"] = self.build_header_fields(exclude=self.exclude_fields)
        context["filter_fields"] = self.build_filter_fields()
        return context

    def build_filter_fields(self):
        filter_fields = []
        filter_fields.append(("position", "Lagerplatz", self.request.GET.get("position", "").strip()))
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
        return filter_queryset_from_position_string(self.request.GET.get("position", "").strip(), model_class)

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


class BookProductToPositionView(LoginRequiredMixin, CreateView):
    template_name = "stock/form.html"
    form_class = StockCreateForm
    login_url = "/login/"

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
        object = form.save(commit=False)
        object.lagerplatz = self.current_position
        print(f"HEROKU 4: {object.id}")
        object.id = Stock.objects.latest("id").id+1
        print(f"HEROKU 5: {object.id}")
        object.save()
        return super().form_valid(form)

    @property
    def current_position(self):
        position = Position.objects.get(id=self.kwargs.get("pk")).position
        print(f"???? {position}")
        return position


class GeneratePositionsView(FormView):
    template_name = "stock/position/generate_positions.html"
    form_class = GeneratePositionsForm
    success_url = reverse_lazy("stock:position_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lagerplätze generieren"
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


from rest_framework import generics
from rest_framework import serializers


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