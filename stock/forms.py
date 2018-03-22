from .models import Stock, Stockdocument
from django.forms import ModelForm
from django import forms


class StockdocumentForm(ModelForm):
    class Meta:
        model = Stockdocument
        exclude = ["id,"]


class ImportForm(forms.Form):
    excel_field = forms.FileField(label="Excel-Datei")