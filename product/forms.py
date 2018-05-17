from django import forms
from django.forms.fields import CharField, FloatField, IntegerField

from product.models import Product


class ImportForm(forms.Form):
    excel_field = forms.FileField(label="Excel-Datei")


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = "__all__"

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
        for visible in self.visible_fields():
            print(type(visible.field))
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField:
                visible.field.widget.attrs["class"] = "form-control"


class ProductIcecatForm(ProductForm):
    class Meta:
        model = Product
        fields = None
        exclude = ["main_image"]