from django.shortcuts import render
from django.views import generic
from django.urls import reverse_lazy
# Create your views here.
from client.forms import ClientForm, ClientCreateForm
from client.models import Client
from contact.models import Contact
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
        contact = Contact(company_image=data.get("company_image"))
        address = Adress(firma=data.get("company"), strasse=data.get("street"), hausnummer=data.get("house_number"),
                         place=data.get("place"), zip=data.get("zip"))
        try:
            address.full_clean()
            address.save()
            contact.adress = address
            contact.full_clean()
            contact.save()
            client.contact = contact
            client.full_clean()
            client.save()
        except ValidationError as e:
            return render(self.request, self.template_name, self.get_context_data())
        return super().form_valid(form)
