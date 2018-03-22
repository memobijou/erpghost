import urllib

from django.shortcuts import render, get_object_or_404
from django.views.generic import FormView
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.forms import modelform_factory
from django_celery_results.models import TaskResult
from import_excel.funcs import get_table_header, check_excel_header_fields_not_in_header, \
    compare_header_with_model_fields, \
    get_records_as_list_with_dicts, check_excel_for_duplicates
from import_excel.models import TaskDuplicates
from .models import Stock, Stockdocument
from .forms import StockdocumentForm
from tablib import Dataset
from .resources import StockResource
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from utils.utils import get_field_names, get_queries_as_json, set_field_names_onview, set_paginated_queryset_onview, \
    filter_queryset_from_request, get_query_as_json, get_related_as_json, get_relation_fields, set_object_ondetailview
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from stock.forms import ImportForm
from stock.tasks import table_data_to_model_task
from erpghost import app


# Create your views here.

class StockListView(LoginRequiredMixin, ListView):
    template_name = "stock/stock_list.html"
    login_url = "/login/"

    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Stock)
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(StockListView, self).get_context_data(*args, **kwargs)

        amount_positions = 30000

        amount_stocks = Stock.objects.count()

        context["amount_positions"] = amount_positions

        context["amount_stocks"] = amount_stocks

        context["progress_bar_value"] = round((100 / amount_positions) * amount_stocks, 2)

        set_field_names_onview(queryset=context["object_list"], context=context, ModelClass=Stock, \
                               exclude_fields=["id", 'regal', "ean_upc", "scanner", "name", "karton",
                                               'box', 'aufnahme_datum', "ignore_unique"], \
                               exclude_filter_fields=["id", "bestand", 'regal', "ean_upc", "scanner", "karton",
                                                      'box', 'aufnahme_datum', "ignore_unique"])
        if context["object_list"]:
            set_paginated_queryset_onview(context["object_list"], self.request, 15, context)

        context["fields"] = self.get_verbose_names(exclude=["id", 'regal', "ean_upc", "scanner", "name", "karton",
                                                            'box', 'aufnahme_datum', "ignore_unique"])
        context["filter_fields"] = self.get_filter_fields(
            exclude=["id", "bestand", 'regal', "ean_upc", "scanner", "karton",
                     'box', 'aufnahme_datum', "ignore_unique"])

        if "table" in str(self.request.get_full_path()):
            context["title"] = "Lagerbestand"
            context["is_table"] = True
        else:
            context["title"] = "Inventar"
            context["is_table"] = None
        # context["extra_fields"] = [("total_amount_ean", "GESAMT")]
        gesamt_arr = []
        for obj in context["object_list"]:
            gesamt_arr.append(obj.total_amount_ean())
        context["gesamt_arr"] = gesamt_arr

        # Auf die Art und WEISE kann man manuell was hinzufügen!! TODO: Dry machen in utils oder so
        if "object_list_as_json" in context:
            new = []
            for json, g in zip(context["object_list_as_json"], gesamt_arr):
                json["GESAMT"] = g
                new.append(json)
            context["object_list_as_json"] = new
        # extra_fields wird in tables noch durchlaufen, der erste Element ist der key, zweite der table header!
        context["extra_fields"] = [("name", "name"), ("GESAMT", "GESAMT")]
        return context

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
        set_object_ondetailview(context=context, ModelClass=Stock, exclude_fields=["id"], \
                                exclude_relations=[], exclude_relation_fields={})
        return context


class StockUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "stock/form.html"
    form_class = modelform_factory(model=Stock, fields=["bestand", "ean_vollstaendig", "zustand", "ignore_unique"],
                                   labels={"bestand": "IST Bestand", "ean_vollstaendig": "EAN"})
    login_url = "/login/"

    def get_object(self):
        object = Stock.objects.get(id=self.kwargs.get("pk"))
        return object

    def get_context_data(self, *args, **kwargs):
        context = super(StockUpdateView, self).get_context_data(*args, **kwargs)
        if not self.request.POST:
            context["object"] = self.get_object(*args, **kwargs)

            context["title"] = "Inventar bearbeiten"

            # context["matching_"] = "Product" # Hier Modelname übergbenen
            # if self.request.POST:
            # 	formset = ProductOrderFormsetInline(self.request.POST, self.request.FILES, instance=self.object)
            # else:
        return context


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

        excel_header_fields = ["ean_vollstaendig", "lagerplatz", "zustand"]
        replace_header_fields = {"ean_vollstaendig": "EAN", "lagerplatz": "Lagerplatz",
                                 "zustand": "Zustand"}  # replace excel_fields with verbose_names to map with model fields

        excel_header_fields_not_in_header = check_excel_header_fields_not_in_header(header, excel_header_fields)

        header_errors = compare_header_with_model_fields(header, Stock, excel_header_fields,
                                                         replace_header_fields=replace_header_fields)

        excel_list = get_records_as_list_with_dicts(file_type, content, header, excel_header_fields,
                                                    replace_header_fields=replace_header_fields)

        excel_duplicates = check_excel_for_duplicates(excel_list)

        if header_errors or excel_header_fields_not_in_header or excel_duplicates:
            context = self.get_context_data(**kwargs)
            context["header_errors"] = header_errors
            context["excel_header_fields_not_in_header"] = excel_header_fields_not_in_header
            context["excel_duplicates"] = excel_duplicates
            return render(self.request, self.template_name, context)

        unique_together = ["EAN", "Lagerplatz", "Zustand"]  # use vebose_names

        table_data_to_model_task.delay(excel_list, ("stock", "Stock"), None, unique_together)
        return super().post(request, *args, **kwargs)
