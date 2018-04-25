from django.shortcuts import render
from django.views import generic

from adress.models import Adress
from contact.models import Contact
from supplier.forms import SupplierModelForm, SupplierForm
from supplier.models import Supplier
from utils.utils import get_verbose_names, get_filter_fields, set_paginated_queryset_onview, \
    filter_queryset_from_request
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError

# Create your views here.


class SupplierListView(generic.ListView):
    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Supplier)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lieferanten"
        set_paginated_queryset_onview(context["object_list"], self.request, 15, context)
        context["fields"] = ["Firma"]
        context["filter_fields"] = get_filter_fields(Supplier, exclude=["id", "contact_id"])
        return context


class SupplierDetailView(generic.DetailView):
    def get_object(self):
        return Supplier.objects.get(pk=self.kwargs.get("pk"))


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
        contact = Contact(adress=address)

        try:
            address.full_clean()
            contact.full_clean()
            supplier.full_clean()

            address.save()
            contact.adress = address
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
        form.initial = {'company': object_.contact.adress.firma,
                        'street': object_.contact.adress.strasse,
                        'zip': object_.contact.adress.zip,
                        'place': object_.contact.adress.place,
                        'house_number': object_.contact.adress.hausnummer, "supplier_number": object_.supplier_number}
        return form

    def form_valid(self, form):
        object_ = self.get_object()
        object_.supplier_number = form.cleaned_data.get("supplier_number")
        object_.contact.adress.firma = form.cleaned_data.get("company")
        object_.contact.adress.strasse = form.cleaned_data.get("street")
        object_.contact.adress.zip = form.cleaned_data.get("zip")
        object_.contact.adress.place = form.cleaned_data.get("place")
        object_.contact.adress.hausnummer = form.cleaned_data.get("house_number")
        try:
            object_.contact.full_clean()
            object_.contact.adress.full_clean()
            object_.full_clean()
            object_.contact.save()
            object_.contact.adress.save()
            object_.contact.save()
            object_.save()
        except ValidationError:
            return render(self.request, self.template_name, self.get_context_data())
        return super().form_valid(form)
