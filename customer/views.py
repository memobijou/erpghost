from django.db.models import Q
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
        queryset = self.filter_queryset_from_request()
        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kunden"
        context["fields"] = ["Kunde"]
        context["fields"].extend(get_verbose_names(Customer, exclude=["id", "contact_id"]))
        context["filter_fields"] = get_filter_fields(Customer, exclude=["id", "contact_id"])
        return context

    def filter_queryset_from_request(self):
        if self.request.GET.get("customer_number") is not None and self.request.GET.get("customer_number") != "":
            q_filter = Q(customer_number__icontains=self.request.GET.get("customer_number").strip())
        else:
            q_filter = Q()
        search_filter = Q()
        search_value = self.request.GET.get("q")

        if search_value is not None and search_value != "":
            search_filter |= Q(customer_number__icontains=search_value.strip())
            search_filter |= Q(contact__billing_address__firma__icontains=search_value.strip())

        q_filter &= search_filter
        return Customer.objects.filter(q_filter).order_by("id")

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
        self.context["billing_forms"] = self.get_billing_addresses()
        self.context["delivery_form"] = self.form_class(prefix="delivery", instance=self.object.contact.delivery_address)
        self.context["delivery_forms"] = self.get_delivery_addresses()
        self.context["new_billing_form"] = self.form_class(prefix="new_billing")
        self.context["new_delivery_form"] = self.form_class(prefix="new_delivery")
        return render(request, self.template_name, self.context)

    def get_billing_addresses(self):
        billing_addresses_forms = []
        count = 1
        for billing_address in self.object.contact.billing_addresses.all():
            billing_addresses_forms.append(self.form_class(prefix=f"billing_{count}", instance=billing_address))
            count += 1
        return billing_addresses_forms

    def get_delivery_addresses(self):
        delivery_addresses_forms = []
        count = 1
        for delivery_address in self.object.contact.delivery_addresses.all():
            delivery_addresses_forms.append(self.form_class(prefix=f"delivery_{count}", instance=delivery_address))
            count += 1
        return delivery_addresses_forms

    def post(self, request, *args, **kwargs):
        print(f"warum ??? {request.POST}")
        billing_form = self.form_class(prefix="billing", data=request.POST)
        delivery_form = self.form_class(prefix="delivery", data=request.POST)

        if "new_billing_subform" in request.POST:
            new_billing_form = self.form_class(prefix="new_billing", data=request.POST)
            if self.create_new_billing_address(new_billing_form) is True:
                return HttpResponseRedirect(self.get_success_url())
            else:
                self.context["billing_form"] = billing_form
                self.context["delivery_form"] = delivery_form
                self.context["new_billing_form"] = new_billing_form
                return render(request, self.template_name, self.context)

        if "new_delivery_subform" in request.POST:
            new_delivery_form = self.form_class(prefix="new_delivery", data=request.POST)
            if self.create_new_delivery_address(new_delivery_form) is True:
                return HttpResponseRedirect(self.get_success_url())
            else:
                self.context["billing_form"] = billing_form
                self.context["delivery_form"] = delivery_form
                self.context["new_delivery_form"] = new_delivery_form
                return render(request, self.template_name, self.context)

        billing_forms = self.billing_forms_call_is_valid()
        billing_forms_are_valid = True
        for b_form in billing_forms:
            if b_form.is_valid() is False:
                billing_forms_are_valid = False

        delivery_forms = self.delivery_forms_call_is_valid()
        delivery_forms_are_valid = True
        for d_form in delivery_forms:
            if d_form.is_valid() is False:
                delivery_forms_are_valid = False

        if billing_form.is_valid() and delivery_form.is_valid() and billing_forms_are_valid is True\
                and delivery_forms_are_valid is True:
            self.update_customer(billing_form, delivery_form, billing_forms, delivery_forms)
            return HttpResponseRedirect(self.get_success_url())
        self.context["billing_form"] = billing_form
        self.context["billing_forms"] = billing_forms
        self.context["delivery_form"] = delivery_form
        self.context["delivery_forms"] = delivery_forms
        self.context["new_billing_form"] = self.form_class(prefix="new_billing", data=request.POST)
        self.context["new_delivery_form"] = self.form_class(prefix="new_delivery", data=request.POST)
        return render(request, self.template_name, self.context)

    def billing_forms_call_is_valid(self):
        billing_addresses_forms = []
        amount_billing_addresses = self.object.contact.billing_addresses.count()
        model_keys = [f.name for f in Adress._meta.get_fields()]
        print(f"akhi 1: {amount_billing_addresses}")
        for i in range(1, amount_billing_addresses+1):
            data = {}
            for field in model_keys:
                value = self.request.POST.get(f"billing_{i}-{field}")
                if value is not None and value != "":
                    data[f"billing_{i}-{field}"] = self.request.POST.get(f"billing_{i}-{field}")
            print(data)
            billing_form = self.form_class(data=data, prefix=f"billing_{i}")
            billing_addresses_forms.append(billing_form)
        return billing_addresses_forms

    def delivery_forms_call_is_valid(self):
        delivery_addresses_forms = []
        amount_delivery_addresses = self.object.contact.delivery_addresses.count()
        model_keys = [f.name for f in Adress._meta.get_fields()]
        for i in range(1, amount_delivery_addresses+1):
            data = {}
            for field in model_keys:
                value = self.request.POST.get(f"delivery_{i}-{field}")
                if value is not None and value != "":
                    data[f"delivery_{i}-{field}"] = self.request.POST.get(f"delivery_{i}-{field}")
            print(data)
            billing_form = self.form_class(data=data, prefix=f"delivery_{i}")
            delivery_addresses_forms.append(billing_form)
        return delivery_addresses_forms

    def update_customer(self, billing_form, delivery_form, billing_forms, delivery_forms):
        print(self.object.contact.billing_address.pk)
        Adress.objects.filter(pk=self.object.contact.billing_address.pk).update(**billing_form.cleaned_data)
        Adress.objects.filter(pk=self.object.contact.delivery_address.pk).update(**delivery_form.cleaned_data)

        count = 0
        for b_address in self.object.contact.billing_addresses.all():
            Adress.objects.filter(pk=b_address.pk).update(**billing_forms[count].cleaned_data)
            count += 1

        count = 0
        for d_address in self.object.contact.delivery_addresses.all():
            Adress.objects.filter(pk=d_address.pk).update(**delivery_forms[count].cleaned_data)
            count += 1

    def create_new_billing_address(self, billing_form):
        if billing_form.is_valid():
            billing_address = billing_form.save()
            self.object.contact.billing_addresses.add(billing_address)
            self.object.contact.save()
            self.object.save()
            return True
        else:
            return False

    def create_new_delivery_address(self, delivery_form):
        if delivery_form.is_valid():
            delivery_address = delivery_form.save()
            self.object.contact.delivery_addresses.add(delivery_address)
            self.object.contact.save()
            self.object.save()
            return True
        else:
            return False


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
