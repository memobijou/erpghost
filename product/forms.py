from django import forms
from django.forms.fields import CharField, FloatField, IntegerField

from product.models import Product


class ImportForm(forms.Form):
    excel_field = forms.FileField(label="Excel-Datei")


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        exclude = ["main_sku"]

    more_images = forms.FileField(label="Weitere Bilder", widget=forms.FileInput(attrs={'multiple': True}),
                                  required=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            print(type(visible.field))
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField:
                visible.field.widget.attrs["class"] = "form-control"


class PurchasingPriceForm(forms.Form):
    purchasing_price = forms.FloatField(label="Einkaufspreis", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['purchasing_price'].widget.attrs['min'] = 0.01

        for visible in self.visible_fields():
            print(type(visible.field))
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField:
                visible.field.widget.attrs["class"] = "form-control"

    def clean_purchasing_price(self):
        purchasing_price = self.cleaned_data['purchasing_price']
        if purchasing_price is not None and purchasing_price < 0.01:
            raise forms.ValidationError("Die Zahl muss größer als 0 sein")
        return purchasing_price


class ProductIcecatForm(ProductForm):
    class Meta:
        model = Product
        fields = None
        exclude = ["main_image"]