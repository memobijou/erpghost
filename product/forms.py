from django import forms
from django.forms.fields import CharField, FloatField, IntegerField

from product.models import Product
from django.urls import reverse_lazy


class ImportForm(forms.Form):
    excel_field = forms.FileField(label="Excel-Datei")


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        exclude = ["main_sku", "single_product"]

    more_images = forms.FileField(label="Weitere Bilder", widget=forms.FileInput(attrs={'multiple': True}),
                                  required=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            print(type(visible.field))
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField:
                visible.field.widget.attrs["class"] = "form-control"

    def clean_ean(self):
        ean = self.cleaned_data['ean'].strip()
        duplicates = Product.objects.filter(ean=ean).exclude(pk=self.instance.pk)
        if duplicates.count() > 0:
            duplicates_html = f""
            for duplicate_product in duplicates:
                img_html = f""
                if duplicate_product.main_image is not None and duplicate_product.main_image != "":
                    img_html += f"<img src='{duplicate_product.main_image.url}' class='img-responsive'" \
                                f" style='max-height:70px;'/>"
                duplicates_html += f"<tr>" \
                                   f"<td>" \
                                   f"<a href='" \
                                   f"{reverse_lazy('product:detail', kwargs={'pk': duplicate_product.pk})}'>" \
                                   f"Ansicht</a><br/>" \
                                   f"<a href='" \
                                   f"{reverse_lazy('product:edit', kwargs={'pk': duplicate_product.pk})}'>" \
                                   f"Bearbeiten</a>" \
                                   f"</td>" \
                                   f"<td>" \
                                   f"{img_html}" \
                                   f"</td>"\
                                   f"<td>{duplicate_product.ean}</td>" \
                                   f"</tr>"
            html_msg =\
                f"Dieser Artikel mit der EAN existiert bereits"
            html_msg += "<div class='table-responsive'><table class='table table-bordered' style='color:black;'>" \
                        "<thead><tr>" \
                        "<th></th>" \
                        "<th>Bild</th>" \
                        "<th>EAN</th>" \
                        "</tr></thead>" \
                        "<tbody>" \
                        f"{duplicates_html}" \
                        "</tbody>" \
                        "</table></div>"
            from django.template import Context
            from django.template import Template
            c = Context({})
            raise forms.ValidationError(Template(html_msg).render(c))
        return ean


class SingleProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["title", "main_image",  "short_description", "description", ]

    state = forms.ChoiceField(choices=((None, "----"), ("Neu", "Neu"), ("B", "B"),
                                       ("C", "C"), ("D", "D"), ("D", "D")), required=True, label="Zustand")

    more_images = forms.FileField(label="Weitere Bilder", widget=forms.FileInput(attrs={'multiple': True}),
                                  required=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            print(type(visible.field))
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField or type(visible.field) is forms.ChoiceField:
                visible.field.widget.attrs["class"] = "form-control"


class SingleProductUpdateForm(SingleProductForm):
    state = None


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