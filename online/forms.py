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
