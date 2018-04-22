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
    street = forms.CharField(max_length=200, label="Straße")
    house_number = forms.CharField(max_length=200, label="Hausnummer")
    zip = forms.CharField(max_length=200, label="PLZ")
    place = forms.CharField(max_length=200, label="Ort")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"