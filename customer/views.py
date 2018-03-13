from django.shortcuts import render
from django.views import generic

from customer.forms import CustomerForm
from customer.models import Customer
from utils.utils import get_verbose_names, get_filter_fields, set_paginated_queryset_onview, \
    filter_queryset_from_request


# Create your views here.

class CustomerListView(generic.ListView):
    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Customer)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kunden"
        set_paginated_queryset_onview(context["object_list"], self.request, 15, context)
        context["fields"] = get_verbose_names(Customer,exclude=["id", "contact_id"])
        context["filter_fields"] = get_filter_fields(Customer, exclude=["id", "contact_id"])
        return context

class CustomerDetailView(generic.DetailView):
    def get_object(self):
        return Customer.objects.get(pk=self.kwargs.get("pk"))

class CustomerCreateView(generic.CreateView):
    form_class = CustomerForm
    template_name = "customer/form.html"

class CustomerUpdateView(generic.UpdateView):
    form_class = CustomerForm
    template_name = "customer/form.html"

    def get_object(self):
        return Customer.objects.get(pk=self.kwargs.get("pk"))
