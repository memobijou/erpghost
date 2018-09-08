from django import forms
from client.models import Client, ApiData


class ClientForm(forms.Form):
    select_client = forms.ModelChoiceField(queryset=Client.objects.all(), label="Mandant auswählen")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class ClientCreateForm(forms.Form):
    name = forms.CharField(max_length=200, label="Bezeichnung")
    billing_company = forms.CharField(max_length=200, label="Firma")
    company_image = forms.ImageField(label="Firmenlogo", required=False)
    billing_first_name = forms.CharField(max_length=200, label="Vorname", required=False)
    billing_last_name = forms.CharField(max_length=200, label="Nachname", required=False)
    billing_street = forms.CharField(max_length=200, label="Straße")
    billing_house_number = forms.CharField(max_length=200, label="Hausnummer")
    billing_zip = forms.CharField(max_length=200, label="PLZ")
    billing_place = forms.CharField(max_length=200, label="Ort")

    delivery_company = forms.CharField(max_length=200, label="Firma")
    delivery_first_name = forms.CharField(max_length=200, label="Vorname", required=False)
    delivery_last_name = forms.CharField(max_length=200, label="Nachname", required=False)
    delivery_street = forms.CharField(max_length=200, label="Straße")
    delivery_house_number = forms.CharField(max_length=200, label="Hausnummer")
    delivery_zip = forms.CharField(max_length=200, label="PLZ")
    delivery_place = forms.CharField(max_length=200, label="Ort")

    phone = forms.CharField(max_length=200, label="Rufnummer")
    fax = forms.CharField(max_length=200, label="Fax")
    email = forms.CharField(max_length=200, label="Email")
    website = forms.CharField(max_length=200, label="Webseite")
    website_conditions_link = forms.CharField(max_length=200, label="AGBs Link", required=False)
    bank = forms.CharField(max_length=200, label="Bank")
    bic = forms.CharField(max_length=200, label="BIC")
    iban = forms.CharField(max_length=200, label="IBAN")
    commercial_register = forms.CharField(max_length=200, label="Handelsregister")
    tax_number = forms.CharField(max_length=200, label="Steuernummer")
    sales_tax_identification_number = forms.CharField(max_length=200, label="Ust-IdNr.")
    qr_code = forms.ImageField(label="QR-Code", required=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"


class ApiDataForm(forms.ModelForm):
    class Meta:
        model = ApiData
        exclude = ["client"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"
