from Crypto.Cipher import AES
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import CreateView, ListView, UpdateView
from configuration.forms import TransportServiceForm, BusinessAccountForm, BusinessAccountFormUpdate, OnlinePositionForm
from django.urls import reverse_lazy
import os

from configuration.models import OnlinePositionPrefix
from disposition.models import TransportService, BusinessAccount


# Create your views here.
from mission.models import PackingStation
from online.forms import PackingStationForm


class TransportServiceList(ListView):
    paginate_by = 15
    template_name = "configuration/transport/list.html"
    queryset = TransportService.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Transportdienstleister Übersicht"
        return context


class BusinessAccountMixin(object):
    def encrypt_password(self, password):
        enc_key = os.environ.get("enc_key")
        print(enc_key)
        iv456 = "randomshit123456"
        encrypt_object = AES.new(enc_key, AES.MODE_CFB, iv456)
        encrypted_string = encrypt_object.encrypt(password)
        return encrypted_string


class CreateTranportService(BusinessAccountMixin, CreateView):
    form_class = TransportServiceForm
    template_name = "configuration/transport/form.html"

    def get_success_url(self):
        return reverse_lazy("config:transport_list")  # zu test erstmal

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Transportdiensleister anlegen"
        context["business_form"] = self.get_business_form()
        return context

    def form_valid(self, form):
        business_form = self.get_business_form()

        if business_form.is_valid() is True:
            transport_service = form.save()
            business_account = business_form.save()
            business_account.transport_service = transport_service
            password = business_form.cleaned_data.get("password")
            password_encrypted = self.encrypt_password(password)
            print(f"--{password_encrypted}")
            print(type(password_encrypted))
            business_account.password_encrypted = password_encrypted.decode("ISO-8859-1")
            business_account.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super().form_invalid(form)

    def get_business_form(self):
        if self.request.method == "POST":
            return BusinessAccountForm(data=self.request.POST)
        else:
            return BusinessAccountForm()


class CreateBusinessAccount(BusinessAccountMixin, CreateView):
    form_class = BusinessAccountForm
    template_name = "configuration/transport/business_form.html"

    def __init__(self, **kwargs):
        self.transport_service = None
        super().__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.transport_service = TransportService.objects.get(pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("config:transport_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["transport_service"] = self.transport_service
        context["title"] = "Geschäftskonto anlegen"
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.transport_service = self.transport_service
        password = form.cleaned_data.get("password")
        if password != "":
            password_encrypted = self.encrypt_password(password)
            print(f"--{password_encrypted}")
            print(type(password_encrypted))
            instance.password_encrypted = password_encrypted.decode("ISO-8859-1")
        return super().form_valid(form)


class UpdateBusinessAccount(BusinessAccountMixin, UpdateView):
    form_class = BusinessAccountFormUpdate
    template_name = "configuration/transport/business_form.html"

    def __init__(self, **kwargs):
        self.transport_service = None
        super().__init__(**kwargs)

    def get_success_url(self):
        return reverse_lazy("config:transport_list")

    def dispatch(self, request, *args, **kwargs):
        self.transport_service = TransportService.objects.get(pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return BusinessAccount.objects.get(pk=self.kwargs.get("business_pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["transport_service"] = self.transport_service
        context["title"] = "Geschäftskonto bearbeiten"
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.transport_service = self.transport_service
        password = form.cleaned_data.get("password")
        if password != "":
            password_encrypted = self.encrypt_password(password)
            print(f"--{password_encrypted}")
            print(type(password_encrypted))
            instance.password_encrypted = password_encrypted.decode("ISO-8859-1")
        return super().form_valid(form)


class OnlinePositionPrefixCreate(CreateView):
    form_class = OnlinePositionForm
    template_name = "configuration/online/position_prefix_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Online Lagerpositionen freigeben"
        return context


class OnlinePositionPrefixUpdate(UpdateView):
    form_class = OnlinePositionForm
    template_name = "configuration/online/position_prefix_form.html"
    success_url = reverse_lazy("config:position_prefix_list")

    def get_object(self, queryset=None):
        return OnlinePositionPrefix.objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Online Lagerpositionen bearbeiten"
        return context


class OnlinePositionPrefixList(ListView):
    paginate_by = 15
    queryset = OnlinePositionPrefix.objects.all()
    template_name = "configuration/online/position_prefix_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Online Lagerpositionen"
        return context


class PackingStationCreate(CreateView):
    form_class = PackingStationForm
    template_name = "configuration/online/packingstation_form.html"
    success_url = reverse_lazy("config:packingstation_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Neue Packstation anlegen"
        return context


class PackingStationList(ListView):
    paginate_by = 15
    queryset = PackingStation.objects.all()
    template_name = "configuration/online/packingstation_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Packstationen Übersicht"
        return context


class PackingStationUpdate(UpdateView):
    form_class = PackingStationForm
    template_name = "configuration/online/packingstation_form.html"
    success_url = reverse_lazy("config:packingstation_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Packstation bearbeiten"
        return context

    def get_object(self, queryset=None):
        return PackingStation.objects.get(pk=self.kwargs.get("pk"))
