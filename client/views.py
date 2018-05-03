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
        return super().form_valid(form)


class ClientCreateView(generic.FormView):
    template_name = "client/form.html"
    form_class = ClientCreateForm
    success_url = reverse_lazy("client:select")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Neuen Mandanten anlegen"
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        client = Client(name=data.get("name"), qr_code=data.get("qr_code"))
        bank = Bank(bank=data.get("bank"), bic=data.get("bic"), iban=data.get("iban"))
        contact = Contact(company_image=data.get("company_image"), telefon=data.get("phone"), fax=data.get("fax"),
                          email=data.get("email"), website=data.get("website"),
                          commercial_register=data.get("commercial_register"), tax_number=data.get("tax_number"),
                          sales_tax_identification_number=data.get("sales_tax_identification_number"))
        billing_address = Adress(firma=data.get("billing_company"), strasse=data.get("billing_street"),
                                 hausnummer=data.get("billing_house_number"),
                                 place=data.get("billing_place"), zip=data.get("billing_zip"),
                                 vorname=data.get("billing_first_name"), nachname=data.get("billing_last_name"))

        delivery_address = Adress(firma=data.get("delivery_company"), strasse=data.get("delivery_street"),
                                  hausnummer=data.get("delivery_house_number"),
                                  place=data.get("delivery_place"), zip=data.get("delivery_zip"),
                                  vorname=data.get("delivery_first_name"), nachname=data.get("delivery_last_name"))

        try:
            billing_address.save()
            delivery_address.save()
            bank.save()
            contact.billing_address = billing_address
            contact.delivery_address = delivery_address
            contact.save()
            contact.bank.add(bank)
            contact.save()
            client.contact = contact
            client.save()
        except ValidationError as e:
            return render(self.request, self.template_name, self.get_context_data())
        return super().form_valid(form)


class ClientUpdateView(generic.FormView):
    template_name = "client/form.html"
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
                "phone": object_.contact.telefon,
                "fax": object_.contact.fax, "email": object_.contact.email, "website": object_.contact.website,
                "commercial_register": object_.contact.commercial_register, "tax_number": object_.contact.tax_number,
                "sales_tax_identification_number": object_.contact.sales_tax_identification_number,
                "qr_code": object_.qr_code
                }

        if object_.contact.delivery_address is not None:
            delivery_data = {
                "delivery_company": object_.contact.delivery_address.firma,
                "delivery_street": object_.contact.delivery_address.strasse,
                "delivery_house_number": object_.contact.delivery_address.hausnummer,
                "delivery_place": object_.contact.delivery_address.place,
                "delivery_zip": object_.contact.delivery_address.zip,
                "delivery_first_name": object_.contact.delivery_address.vorname,
                "delivery_last_name": object_.contact.delivery_address.nachname,
            }
            data.update(delivery_data)

        if object_.contact.billing_address is not None:
            billing_data = {
                "billing_company": object_.contact.billing_address.firma,
                "billing_street": object_.contact.billing_address.strasse,
                "billing_house_number": object_.contact.billing_address.hausnummer,
                "billing_place": object_.contact.billing_address.place,
                "billing_zip": object_.contact.billing_address.zip,
                "billing_first_name": object_.contact.billing_address.vorname,
                "billing_last_name": object_.contact.billing_address.nachname,
            }
            data.update(billing_data)

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
        client.contact.telefon = data.get("phone")
        client.contact.fax = data.get("fax")
        client.contact.email = data.get("email")
        client.contact.website = data.get("website")
        client.contact.commercial_register = data.get("commercial_register")
        client.contact.tax_number = data.get("tax_number")
        client.contact.sales_tax_identification_number = data.get("sales_tax_identification_number")

        billing_address = client.contact.billing_address
        if billing_address is None:
            billing_address = Adress()

        billing_address.firma = data.get("billing_company")
        billing_address.strasse = data.get("billing_street")
        billing_address.hausnummer = data.get("billing_house_number")
        billing_address.place = data.get("billing_place")
        billing_address.zip = data.get("billing_zip")
        billing_address.vorname = data.get("billing_first_name")
        billing_address.nachname = data.get("billing_last_name")

        delivery_address = client.contact.delivery_address
        if delivery_address is None:
            delivery_address = Adress()

        delivery_address.firma = data.get("delivery_company")
        delivery_address.strasse = data.get("delivery_street")
        delivery_address.hausnummer = data.get("delivery_house_number")
        delivery_address.place = data.get("delivery_place")
        delivery_address.zip = data.get("delivery_zip")
        delivery_address.vorname = data.get("delivery_first_name")
        delivery_address.nachname = data.get("delivery_last_name")

        if data.get("qr_code") is False:
            client.qr_code.delete()
        else:
            client.qr_code = data.get("qr_code")

        if data.get("company_image") is False:
            client.contact.company_image.delete()
        else:
            client.contact.company_image = data.get("company_image")

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
            billing_address.save()
            delivery_address.save()
            client.contact.billing_address = billing_address
            client.contact.delivery_address = delivery_address
            client.contact.save()
            client.save()
        except ValidationError as e:
            return render(self.request, self.template_name, self.get_context_data())
        return super().form_valid(form)
