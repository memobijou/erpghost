from django import forms
from client.models import Client


class ClientForm(forms.Form):
    select_client = forms.ModelChoiceField(queryset=Client.objects.all(), label="Mandant auswählen")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class ClientCreateForm(forms.Form):
    name = forms.CharField(max_length=200, label="Bezeichnung")
    company = forms.CharField(max_length=200, label="Firma")
    company_image = forms.ImageField(label="Firmenlogo")
    first_name = forms.CharField(max_length=200, label="Vorname", required=False)
    last_name = forms.CharField(max_length=200, label="Nachname", required=False)
    street = forms.CharField(max_length=200, label="Straße")
    house_number = forms.CharField(max_length=200, label="Hausnummer")
    zip = forms.CharField(max_length=200, label="PLZ")
    place = forms.CharField(max_length=200, label="Ort")
    phone = forms.CharField(max_length=200, label="Rufnummer")
    fax = forms.CharField(max_length=200, label="Fax")
    email = forms.CharField(max_length=200, label="Email")
    website = forms.CharField(max_length=200, label="Webseite")
    bank = forms.CharField(max_length=200, label="Bank")
    bic = forms.CharField(max_length=200, label="BIC")
    iban = forms.CharField(max_length=200, label="IBAN")
    commercial_register = forms.CharField(max_length=200, label="Handelsregister")
    tax_number = forms.CharField(max_length=200, label="Steuernummer")
    sales_tax_identification_number = forms.CharField(max_length=200, label="Ust-IdNr.")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"
