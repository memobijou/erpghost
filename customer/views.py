from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import generic
from django.urls import reverse_lazy
from django.views.generic import DeleteView

from adress.models import Adress
from contact.models import Contact
from customer.forms import CustomerForm, AddressForm
from customer.models import Customer
from utils.utils import get_verbose_names, get_filter_fields, set_paginated_queryset_onview, \
    filter_queryset_from_request
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django import views
# Create your views here.


class CustomerListView(generic.ListView):
    template_name = "customer/customer_list.html"

    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Customer).order_by("-id")
        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kunden"
        context["fields"] = ["Kunde"]
        context["fields"].extend(get_verbose_names(Customer, exclude=["id", "contact_id"]))
        context["filter_fields"] = get_filter_fields(Customer, exclude=["id", "contact_id"])
        return context

    def set_pagination(self, queryset):
        page = self.request.GET.get("page")
        paginator = Paginator(queryset, 15)
        if not page:
            page = 1
        current_page_object = paginator.page(int(page))
        return current_page_object


class CustomerDetailView(generic.DetailView):
    def get_object(self):
        return Customer.objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kunde Ansicht"
        return context


class CustomerCreateView(views.View):
    template_name = "customer/form.html"
    success_url = reverse_lazy("customer:list")
    form_class = AddressForm
    context = {}

    def get(self, request, *args, **kwargs):
        self.context["title"] = "Neuen Kunden anlegen"
        self.context["billing_form"] = self.form_class(prefix="billing")
        self.context["delivery_form"] = self.form_class(prefix="delivery")
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        billing_form = self.form_class(prefix="billing", data=request.POST)
        delivery_form = self.form_class(prefix="delivery", data=request.POST)

        if billing_form.is_valid() and delivery_form.is_valid():
            self.save_new_customer(billing_form, delivery_form)
            return HttpResponseRedirect(self.success_url)
        self.context["billing_form"] = billing_form
        self.context["delivery_form"] = delivery_form
        print(self.context)
        return render(request, self.template_name, self.context)

    def save_new_customer(self, billing_form, delivery_form):
        contact = Contact()
        billing_address = billing_form.save()
        delivery_address = delivery_form.save()
        contact.billing_address = billing_address
        contact.delivery_address = delivery_address
        contact.save()
        customer = Customer()
        customer.contact = contact
        customer.save()


class CustomerUpdateView(views.View):
    form_class = AddressForm
    template_name = "customer/form.html"
    object = None
    context = {}

    def dispatch(self, request, *args, **kwargs):
        self.object = Customer.objects.get(pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.object

    def get_success_url(self):
        return reverse_lazy("customer:detail", kwargs={"pk": self.kwargs.get("pk")})

    def get(self, request, *args, **kwargs):
        self.context["title"] = "Kunden bearbeiten"
        self.context["billing_form"] = self.form_class(prefix="billing", instance=self.object.contact.billing_address)
        self.context["delivery_form"] = self.form_class(prefix="delivery", instance=self.object.contact.delivery_address)
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        billing_form = self.form_class(prefix="billing", data=request.POST)
        delivery_form = self.form_class(prefix="delivery", data=request.POST)

        if billing_form.is_valid() and delivery_form.is_valid():
            self.update_customer(billing_form, delivery_form)
            return HttpResponseRedirect(self.get_success_url())
        self.context["billing_form"] = billing_form
        self.context["delivery_form"] = delivery_form
        print(self.context)
        return render(request, self.template_name, self.context)

    def update_customer(self, billing_form, delivery_form):
        billing_address = billing_form.save()
        delivery_address = delivery_form.save()
        self.object.contact.billing_address = billing_address
        self.object.contact.delivery_address = delivery_address
        self.object.contact.save()
        self.object.save()


class CustomerDeleteView(DeleteView):
    model = Customer
    success_url = reverse_lazy("customer:list")
    template_name = "customer/customer_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kunden löschen"
        context["delete_items"] = self.get_object()
        return context

    def get_object(self, queryset=None):
        return Customer.objects.filter(id__in=self.request.GET.getlist('item')).order_by("-id")
