from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import generic
from django.views.generic import DeleteView

from adress.models import Adress
from contact.models import Contact
from supplier.forms import SupplierModelForm, SupplierForm, AddressForm
from supplier.models import Supplier
from utils.utils import get_verbose_names, get_filter_fields, set_paginated_queryset_onview, \
    filter_queryset_from_request
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django import views
# Create your views here.


class SupplierListView(generic.ListView):
    template_name = "supplier/supplier_list.html"

    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Supplier).order_by("-id")
        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lieferanten"
        context["fields"] = ["Lieferant"]
        context["fields"].extend(get_verbose_names(Supplier, exclude=["id", "contact_id"]))
        context["filter_fields"] = get_filter_fields(Supplier, exclude=["id", "contact_id"])
        return context

    def set_pagination(self, queryset):
        page = self.request.GET.get("page")
        paginator = Paginator(queryset, 15)
        if not page:
            page = 1
        current_page_object = paginator.page(int(page))
        return current_page_object


class SupplierDetailView(generic.DetailView):
    def get_object(self):
        return Supplier.objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lieferant Ansicht"
        return context


class SupplierCreateView(views.View):
    template_name = "supplier/form.html"
    success_url = reverse_lazy("supplier:list")
    form_class = AddressForm
    context = {}

    def get(self, request, *args, **kwargs):
        self.context["title"] = "Neuen Lieferanten anlegen"
        self.context["billing_form"] = self.form_class(prefix="billing")
        self.context["delivery_form"] = self.form_class(prefix="delivery")
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        billing_form = self.form_class(prefix="billing", data=request.POST)
        delivery_form = self.form_class(prefix="delivery", data=request.POST)

        if billing_form.is_valid() and delivery_form.is_valid():
            self.save_new_supplier(billing_form, delivery_form)
            return HttpResponseRedirect(self.success_url)
        self.context["billing_form"] = billing_form
        self.context["delivery_form"] = delivery_form
        return render(request, self.template_name, self.context)

    def save_new_supplier(self, billing_form, delivery_form):
        contact = Contact()
        billing_address = billing_form.save()
        delivery_address = delivery_form.save()
        contact.billing_address = billing_address
        contact.delivery_address = delivery_address
        contact.save()
        supplier = Supplier()
        supplier.contact = contact
        supplier.save()


class SupplierUpdateView(views.View):
    form_class = AddressForm
    template_name = "supplier/form.html"
    object = None
    context = {}

    def dispatch(self, request, *args, **kwargs):
        self.object = Supplier.objects.get(pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.object

    def get_success_url(self):
        return reverse_lazy("supplier:detail", kwargs={"pk": self.kwargs.get("pk")})

    def get(self, request, *args, **kwargs):
        self.context["title"] = "Lieferanten bearbeiten"
        self.context["billing_form"] = self.form_class(prefix="billing", instance=self.object.contact.billing_address)
        self.context["delivery_form"] = self.form_class(prefix="delivery", instance=self.object.contact.delivery_address)
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        billing_form = self.form_class(prefix="billing", data=request.POST)
        delivery_form = self.form_class(prefix="delivery", data=request.POST)

        if billing_form.is_valid() and delivery_form.is_valid():
            self.update_supplier(billing_form, delivery_form)
            return HttpResponseRedirect(self.get_success_url())
        self.context["billing_form"] = billing_form
        self.context["delivery_form"] = delivery_form
        print(self.context)
        return render(request, self.template_name, self.context)

    def update_supplier(self, billing_form, delivery_form):
        billing_address = billing_form.save()
        delivery_address = delivery_form.save()
        self.object.contact.billing_address = billing_address
        self.object.contact.delivery_address = delivery_address
        self.object.contact.save()
        self.object.save()


class SupplierDeleteView(DeleteView):
    model = Supplier
    success_url = reverse_lazy("supplier:list")
    template_name = "supplier/supplier_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lieferanten löschen"
        context["delete_items"] = self.get_object()
        return context

    def get_object(self, queryset=None):
        return Supplier.objects.filter(id__in=self.request.GET.getlist('item')).order_by("-id")
