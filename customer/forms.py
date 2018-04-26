from django import forms
from customer.models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = "__all__"


class CustomerForm(forms.Form):
    company = forms.CharField(max_length=200, label="Firma")
    street = forms.CharField(max_length=200, label="Straße")
    house_number = forms.CharField(max_length=200, label="Hausnummer")
    place = forms.CharField(max_length=200, label="Ort")
    zip = forms.CharField(max_length=200, label="PLZ")
    customer_number = forms.CharField(max_length=200, label="Kundennummer")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
