import urllib

from django.shortcuts import render, get_object_or_404
from django.views.generic import FormView
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.forms import modelform_factory
from django_celery_results.models import TaskResult
from import_excel.funcs import get_table_header, check_excel_for_duplicates
from stock.funcs import get_records_as_list_with_dicts
from import_excel.models import TaskDuplicates
from product.models import Product
from .models import Stock, Stockdocument
from .forms import StockdocumentForm, StockForm
from tablib import Dataset
from .resources import StockResource
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from utils.utils import filter_queryset_from_request, set_object_ondetailview
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from stock.forms import ImportForm
from stock.tasks import table_data_to_model_task
from erpghost import app
from django.core.paginator import Paginator


# Create your views here.

class StockListView(LoginRequiredMixin, ListView):
    template_name = "stock/stock_list.html"
    login_url = "/login/"

    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Stock).order_by("-id")
        return self.set_pagination(queryset)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context["fields"] = self.build_fields()

        context["object_list"] = self.get_queryset()

        context["object_list_zip"] = zip(context["object_list"], self.get_products())

        context["filter_fields"] = self.get_filter_fields(
            exclude=["id", "bestand", 'regal', "ean_upc", "scanner", "karton",
                     'box', 'aufnahme_datum', "ignore_unique"])

        context["title"] = "Lagerbestand"

        return context

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
            product = Product.objects.filter(ean=q.ean_vollstaendig).first()
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
        context = super(StockDetailView, self).get_context_data(*args, **kwargs)
        context["title"] = "Inventar " + context["object"].lagerplatz
        context["product"] = Product.objects.filter(ean=self.object.ean_vollstaendig).first()
        return context


class StockUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "stock/form.html"
    form_class = StockForm
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


class StockCopyView(StockUpdateView):
    def get_object(self):
        copy = Stock.objects.get(pk=self.kwargs.get("pk"))
        copy.id = None
        copy.ean_vollstaendig = None
        copy.zustand = "Neu"
        copy.bestand = None
        copy.title = None
        copy.sku = None
        copy.name = None
        copy.regal = None
        copy.karton = None
        copy.box = None
        copy.aufnahme_datum = None
        copy.scanner = None
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
