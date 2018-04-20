from .models import Stock, Stockdocument
from django.forms import ModelForm, CharField, FloatField, IntegerField
from django import forms


class StockdocumentForm(ModelForm):
    class Meta:
        model = Stockdocument
        exclude = ["id,"]


class ImportForm(forms.Form):
    excel_field = forms.FileField(label="Excel-Datei")


class StockUpdateForm(ModelForm):
    class Meta:
        model = Stock
        fields = ["zustand", "ean_vollstaendig", "sku", "title", "bestand"]
        labels = {"bestand": "IST Bestand", "ean_vollstaendig": "EAN"}
    zustand = forms.ChoiceField(choices=(("Neu", "Neu"),("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")),
                                label=Stock._meta.get_field('zustand').verbose_name)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['bestand'].required = True
        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField or type(visible.field) is forms.ChoiceField:
                visible.field.widget.attrs["class"] = "form-control"


class StockCreateForm(ModelForm):
    class Meta:
        model = Stock
        fields = ["zustand", "ean_vollstaendig", "sku", "title", "bestand", "lagerplatz"]
        labels = {"bestand": "IST Bestand", "ean_vollstaendig": "EAN"}
    zustand = forms.ChoiceField(choices=(("Neu", "Neu"),("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")),
                                label=Stock._meta.get_field('zustand').verbose_name)
    lagerplatz = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['bestand'].required = True

        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField or type(visible.field) is forms.ChoiceField:
                visible.field.widget.attrs["class"] = "form-control"


class GeneratePositionsForm(forms.Form):
    prefix = forms.CharField(label='Prefix', max_length=100)
    shelf_number = forms.IntegerField(label='Regalnummer')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField or type(visible.field) is forms.ChoiceField:
                visible.field.widget.attrs["class"] = "form-control"


number_choices = [(i, i) for i in range(1, 201)]


class GeneratePositionLevelsColumnsForm(forms.Form):
    level = forms.ChoiceField(choices=number_choices, label='Ebene', required=True)
    columns_from = forms.ChoiceField(choices=[(None, "----")] + number_choices, label='Anzahl Spalten von', required=True)
    columns_to = forms.ChoiceField(choices=[(None, "----")] + number_choices, label='Anzahl Spalten bis', required=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField or type(visible.field) is forms.ChoiceField:
                visible.field.widget.attrs["class"] = "form-control"
