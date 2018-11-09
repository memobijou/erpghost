from django import forms
from adress.models import Adress
from mission.models import Mission, PickList, PickListProducts, PackingStation
from django.core.exceptions import NON_FIELD_ERRORS


class DhlForm(forms.ModelForm):
    class Meta:
        model = Adress
        fields = ("first_name_last_name", 'strasse', "hausnummer", "zip", "place")
    package_weight = forms.FloatField(label="Paketgewicht in KG", required=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class DPDForm(forms.ModelForm):
    class Meta:
        model = Adress
        fields = ("first_name_last_name", 'strasse', "hausnummer", "zip", "place")
    package_weight = forms.FloatField(label="Paketgewicht in KG", required=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class AcceptOnlinePicklistForm(forms.ModelForm):
    class Meta:
        model = PickList
        fields = ["pick_id"]


class PickListProductsForm(forms.ModelForm):
    class Meta:
        model = PickListProducts
        fields = ["picked"]


class PackingStationForm(forms.ModelForm):
    class Meta:
        model = PackingStation
        fields = ["prefix", "station_number"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class StationGotoPickListForm(forms.Form):
    ean = forms.CharField(max_length=13, label="EAN", help_text="<div class='help-block'>Bitte scannen Sie einen "
                                                                "Artikel auf der Station, um einen Auftrag zu öffnen"
                                                                "</div>")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class PackingForm(forms.Form):
    ean = forms.CharField(max_length=13, label="EAN", help_text="<div class='help-block'>Bitte scannen Sie einen "
                                                                "Artikel"
                                                                "</div>")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class BookinForm(forms.Form):
    bookin_amount = forms.IntegerField(required=True, label="Menge")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class ImportForm(forms.Form):
    import_file = forms.FileField(label="Import Datei", required=True)


class ConfirmManualForm(forms.Form):
    note = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", "rows": 5}), required=False,
                           label="Bemerkung")
