from django import forms
from supplier.models import Supplier


class SupplierModelForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = "__all__"


class SupplierForm(forms.Form):
    company = forms.CharField(max_length=200, label="Firma")
    street = forms.CharField(max_length=200, label="Straße")
    house_number = forms.CharField(max_length=200, label="Hausnummer")
    place = forms.CharField(max_length=200, label="Ort")
    zip = forms.CharField(max_length=200, label="PLZ")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
