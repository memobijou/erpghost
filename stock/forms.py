from .models import Stock, Stockdocument
from django.forms import ModelForm


class StockdocumentForm(ModelForm):
    class Meta:
        model = Stockdocument
        exclude = ['id', ]
