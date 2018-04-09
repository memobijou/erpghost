from .models import Stock, Stockdocument
from django.forms import ModelForm, CharField, FloatField, IntegerField
from django import forms


class StockdocumentForm(ModelForm):
    class Meta:
        model = Stockdocument
        exclude = ["id,"]


class ImportForm(forms.Form):
    excel_field = forms.FileField(label="Excel-Datei")


class StockForm(ModelForm):
    class Meta:
        model = Stock
        fields = ["ean_vollstaendig", "sku", "title",  "zustand", "bestand"]
        labels = {"bestand": "IST Bestand", "ean_vollstaendig": "EAN"}
    zustand = forms.ChoiceField(choices=(("Neu", "Neu"),("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")),
                                label=Stock._meta.get_field('zustand').verbose_name)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField or type(visible.field) is forms.ChoiceField:
                visible.field.widget.attrs["class"] = "form-control"
