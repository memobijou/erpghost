from django.shortcuts import render
from django.views import generic
from django.urls import reverse_lazy
# Create your views here.
from client.forms import ClientForm, ClientCreateForm
from client.models import Client
from contact.models import Contact, Bank
from adress.models import Adress
from django.core.exceptions import ValidationError


class ClientSelectView(generic.FormView):
    template_name = "client/select_client.html"
    form_class = ClientForm
    success_url = reverse_lazy("client:select")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Mandant auswählen"
        if self.request.session.get("client") is not None:
            context["current_client"] = Client.objects.get(pk=self.request.session.get("client"))
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        self.request.session["client"] = data.get("select_client").pk
        self.request.session["client_name"] = data.get("select_client").name

        print(self.request.session.get("client"))
        return super().form_valid(form)


class ClientCreateView(generic.FormView):
    template_name = "client/create_client.html"
    form_class = ClientCreateForm
    success_url = reverse_lazy("client:select")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Neuen Mandanten anlegen"
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        client = Client(name=data.get("name"))
        bank = Bank(bank=data.get("bank"), bic=data.get("bic"), iban=data.get("iban"))
        contact = Contact(company_image=data.get("company_image"), telefon=data.get("phone"), fax=data.get("fax"),
                          email=data.get("email"), website=data.get("website"),
                          commercial_register=data.get("commercial_register"), tax_number=data.get("tax_number"),
                          sales_tax_identification_number=data.get("sales_tax_identification_number"))
        address = Adress(firma=data.get("company"), strasse=data.get("street"), hausnummer=data.get("house_number"),
                         place=data.get("place"), zip=data.get("zip"),
                         vorname=data.get("first_name"), nachname=data.get("last_name"))
        try:
            address.save()
            bank.save()
            contact.adress = address
            contact.save()
            contact.bank.add(bank)
            contact.save()
            client.contact = contact
            client.save()
        except ValidationError as e:
            return render(self.request, self.template_name, self.get_context_data())
        return super().form_valid(form)


class ClientUpdateView(generic.FormView):
    template_name = "client/create_client.html"
    form_class = ClientCreateForm
    success_url = reverse_lazy("client:select")

    def get_object(self):
        return Client.objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Mandanten bearbeiten"
        return context

    def get_form(self, form_class=None):
        object_ = self.get_object()
        data = {"name": object_.name, "company_image": object_.contact.company_image,
                "company": object_.contact.adress.firma, "street": object_.contact.adress.strasse,
                "house_number": object_.contact.adress.hausnummer, "place": object_.contact.adress.place,
                "zip": object_.contact.adress.zip, "phone": object_.contact.telefon, "fax": object_.contact.fax,
                "email": object_.contact.email, "website": object_.contact.website,
                "commercial_register": object_.contact.commercial_register, "tax_number": object_.contact.tax_number,
                "sales_tax_identification_number": object_.contact.sales_tax_identification_number,
                "first_name": object_.contact.adress.vorname, "last_name": object_.contact.adress.nachname
                }
        if object_.contact.bank.first() is not None:
            data["bank"] = object_.contact.bank.first().bank
            data["bic"] = object_.contact.bank.first().bic
            data["iban"] = object_.contact.bank.first().iban
        form = super().get_form(form_class)
        form.initial = data
        return form

    def form_valid(self, form):
        data = form.cleaned_data
        client = self.get_object()
        client.name = data.get("name")
        client.contact.company_image = data.get("company_image")
        client.contact.telefon = data.get("phone")
        client.contact.fax = data.get("fax")
        client.contact.email = data.get("email")
        client.contact.website = data.get("website")
        client.contact.commercial_register = data.get("commercial_register")
        client.contact.tax_number = data.get("tax_number")
        client.contact.sales_tax_identification_number = data.get("sales_tax_identification_number")
        client.contact.adress.firma = data.get("company")
        client.contact.adress.strasse = data.get("street")
        client.contact.adress.hausnummer = data.get("house_number")
        client.contact.adress.place = data.get("place")
        client.contact.adress.zip = data.get("zip")
        client.contact.adress.vorname = data.get("first_name")
        client.contact.adress.nachname = data.get("last_name")

        if client.contact.bank.first() is None:
            bank = Bank(bank=data.get("bank"), bic=data.get("bic"), iban=data.get("iban"))
            bank.save()
            client.contact.bank.add(bank)
        if client.contact.bank.first() is not None:
            bank = client.contact.bank.first()
            bank.bank = data.get("bank")
            bank.bic = data.get("bic")
            bank.iban = data.get("iban")
            bank.save()

        print(f"Hero: {client.contact.bank.first()}")

        try:
            client.contact.adress.save()
            client.contact.save()
            client.save()
        except ValidationError as e:
            return render(self.request, self.template_name, self.get_context_data())
        return super().form_valid(form)
