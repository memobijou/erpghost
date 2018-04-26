from django.shortcuts import render
from django.views import generic
from django.urls import reverse_lazy
from adress.models import Adress
from contact.models import Contact
from customer.forms import CustomerForm
from customer.models import Customer
from utils.utils import get_verbose_names, get_filter_fields, set_paginated_queryset_onview, \
    filter_queryset_from_request
from django.core.exceptions import ValidationError


# Create your views here.

class CustomerListView(generic.ListView):
    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Customer)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kunden"
        set_paginated_queryset_onview(context["object_list"], self.request, 15, context)
        context["fields"] = ["Kunde"]
        context["fields"].extend(get_verbose_names(Customer, exclude=["id", "contact_id"]))
        context["filter_fields"] = get_filter_fields(Customer, exclude=["id", "contact_id"])
        return context


class CustomerDetailView(generic.DetailView):
    def get_object(self):
        return Customer.objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kunde Ansicht"
        return context


class CustomerCreateView(generic.FormView):
    form_class = CustomerForm
    template_name = "customer/form.html"
    success_url = reverse_lazy("customer:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kunden anlegen"
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        customer = Customer(customer_number=data.get("customer_number"))
        address = Adress(firma=data.get("company"), zip=data.get("zip"), place=data.get("place"),
                         strasse=data.get("street"), hausnummer=data.get("house_number"))
        contact = Contact(billing_address=address)

        try:
            address.full_clean()
            contact.full_clean()
            customer.full_clean()

            address.save()
            contact.billing_address = address
            contact.save()
            customer.contact = contact
            customer.save()
        except ValidationError as e:
            return render(self.request, self.template_name, self.get_context_data())
        return super().form_valid(form)


class CustomerUpdateView(generic.FormView):
    form_class = CustomerForm
    template_name = "customer/form.html"
    object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = Customer.objects.get(pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.object

    def get_success_url(self):
        return reverse_lazy("customer:detail", kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context["title"] = "Kunden bearbeiten"
            context["object"] = self.get_object()
            return context

    def get_form(self, form_class=None):
        form = super().get_form()
        object_ = self.get_object()
        print(object_.contact)
        if object_.contact is None or object_.contact.billing_address is None:
            form.initial = {"customer_number": object_.customer_number}
            return form
        form.initial = {'company': object_.contact.billing_address.firma,
                        'street': object_.contact.billing_address.strasse,
                        'zip': object_.contact.billing_address.zip,
                        'place': object_.contact.billing_address.place,
                        'house_number': object_.contact.billing_address.hausnummer,
                        "customer_number": object_.customer_number}
        return form

    def form_valid(self, form):
        object_ = self.get_object()
        object_.customer_number = form.cleaned_data.get("customer_number")
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
