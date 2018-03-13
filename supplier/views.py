from django.shortcuts import render
from django.views import generic

from supplier.forms import SupplierForm
from supplier.models import Supplier
from utils.utils import get_verbose_names, get_filter_fields, set_paginated_queryset_onview, \
    filter_queryset_from_request


# Create your views here.

class SupplierListView(generic.ListView):
    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Supplier)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lieferanten"
        set_paginated_queryset_onview(context["object_list"], self.request, 15, context)
        context["fields"] = get_verbose_names(Supplier,exclude=["id", "contact_id"])
        context["filter_fields"] = get_filter_fields(Supplier, exclude=["id", "contact_id"])
        return context

class SupplierDetailView(generic.DetailView):
    def get_object(self):
        return Supplier.objects.get(pk=self.kwargs.get("pk"))

class SupplierCreateView(generic.CreateView):
    form_class = SupplierForm
    template_name = "supplier/form.html"

class SupplierUpdateView(generic.UpdateView):
    form_class = SupplierForm
    template_name = "supplier/form.html"

    def get_object(self):
        return Supplier.objects.get(pk=self.kwargs.get("pk"))
