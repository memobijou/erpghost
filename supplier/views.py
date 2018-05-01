from django.shortcuts import render
from django.views import generic
from django.views.generic import DeleteView

from adress.models import Adress
from contact.models import Contact
from supplier.forms import SupplierModelForm, SupplierForm
from supplier.models import Supplier
from utils.utils import get_verbose_names, get_filter_fields, set_paginated_queryset_onview, \
    filter_queryset_from_request
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
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


class SupplierCreateView(generic.FormView):
    form_class = SupplierForm
    template_name = "supplier/form.html"
    success_url = reverse_lazy("supplier:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lieferanten anlegen"
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        supplier = Supplier()
        address = Adress(firma=data.get("company"), zip=data.get("zip"), place=data.get("place"),
                         strasse=data.get("street"), hausnummer=data.get("house_number"))
        contact = Contact(billing_address=address)

        try:
            address.save()
            contact.billing_address = address
            contact.save()
            supplier.contact = contact
            supplier.save()
        except ValidationError as e:
            return render(self.request, self.template_name, self.get_context_data())
        return super().form_valid(form)


class SupplierUpdateView(generic.FormView):
    form_class = SupplierForm
    template_name = "supplier/form.html"
    object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = Supplier.objects.get(pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.object

    def get_success_url(self):
        return reverse_lazy("supplier:detail", kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context["title"] = "Lieferant bearbeiten"
            context["object"] = self.get_object()
            return context

    def get_form(self, form_class=None):
        form = super().get_form()
        object_ = self.get_object()
        if object_.contact is None or object_.contact.billing_address is None:
            form.initial = {"supplier_number": object_.supplier_number}
            return form
        form.initial = {'company': object_.contact.billing_address.firma,
                        'street': object_.contact.billing_address.strasse,
                        'zip': object_.contact.billing_address.zip,
                        'place': object_.contact.billing_address.place,
                        'house_number': object_.contact.billing_address.hausnummer,
                        }
        return form

    def form_valid(self, form):
        object_ = self.get_object()
        contact = object_.contact
        if contact is None:
            contact = Contact()
            contact.billing_address = Adress()
        if contact is not None and contact.billing_address is None:
            contact.billing_address = Adress()
        contact.billing_address.firma = form.cleaned_data.get("company")
        contact.billing_address.strasse = form.cleaned_data.get("street")
        contact.billing_address.zip = form.cleaned_data.get("zip")
        contact.billing_address.place = form.cleaned_data.get("place")
        contact.billing_address.hausnummer = form.cleaned_data.get("house_number")
        try:
            billing_address = contact.billing_address
            billing_address.save()
            contact.billing_address = billing_address
            contact.save()
            object_.contact = contact
            object_.save()
        except ValidationError:
            return render(self.request, self.template_name, self.get_context_data())
        return super().form_valid(form)


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
