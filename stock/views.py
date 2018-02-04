from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.forms import modelform_factory
from .models import Stock, Stockdocument
from .forms import StockdocumentForm
from tablib import Dataset
from tablib import formats
from .resources import StockResource
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from utils.utils import get_field_names, get_queries_as_json, set_field_names_onview, set_paginated_queryset_onview, \
    filter_queryset_from_request, get_query_as_json, get_related_as_json, get_relation_fields, set_object_ondetailview
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages


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
                               exclude_filter_fields=["id", "bestand", 'regal', "ean_upc", "scanner", "name", "karton",
                                                      'box', 'aufnahme_datum', "ignore_unique"])
        if context["object_list"]:
            set_paginated_queryset_onview(context["object_list"], self.request, 15, context)

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
        context["extra_fields"] = [("GESAMT", "GESAMT")]
        return context


class StockCreateView(LoginRequiredMixin, CreateView):
    template_name = "stock/stock_create.html"
    form_class = StockdocumentForm
    login_url = "/login/"

    def form_valid(self, form, *args, **kwargs):

        stock_resource = StockResource()
        dataset = Dataset()
        dataset.headers = ('id',
                           'ean_vollstaendig', 'bestand', 'ean_upc', 'lagerplatz', 'regal', 'zustand', 'scanner',
                           'name', 'karton',
                           'box',
                           'aufnahme_datum', 'ignore_unique')
        document = form.cleaned_data["document"]

        imported_data = dataset.load(document.read())
        dataset.insert_col(0, lambda r: "", header='id')

        duplicate = check_duplicate_inside_excel(imported_data)

        if duplicate:
            messages.error(self.request, 'Doppelter Eintrag in <b>Exceldatei</b>!')
            messages.error(self.request, duplicate)
            super(StockCreateView, self).form_valid(form)
            return HttpResponseRedirect(self.request.path_info)

        for row in imported_data:
            if Stock.objects.filter(lagerplatz=row[4], ean_vollstaendig=row[1], zustand=row[6]).exists():
                messages.error(self.request, 'Eintrag in <b>Datenbank</b> vorhanden!')
                messages.error(self.request, f"{row[1]} - {row[4]} - {row[6]} ")
                print(f"{row[1]} - {row[4]} - {row[6]} ")
                super(StockCreateView, self).form_valid(form)
                return HttpResponseRedirect(self.request.path_info)
        result = stock_resource.import_data(dataset, dry_run=True)  # Test the data import
        if not result.has_errors():
            stock_resource.import_data(dataset, dry_run=False)  # Actually import now
        else:
            super(StockCreateView, self).form_valid(form)
            return HttpResponseRedirect(self.get_success_url())
        messages.success(self.request, f"{document} erfolgreich hochgeladen!")
        super(StockCreateView, self).form_valid(form)
        return HttpResponseRedirect(self.get_success_url())


def check_duplicate_inside_excel(arr):
    for i, row in enumerate(arr):
        for j, against_row in enumerate(arr):
            if i != j:
                if row[1] == against_row[1] and row[4] == against_row[4] and row[6] == against_row[6]:
                    print(f"{row[1]} - {row[4]} - {row[6]} " \
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
