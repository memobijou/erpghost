from django import forms
from adress.models import Adress
from mission.models import Mission, PickList, PickListProducts, PackingStation, Shipment
from django.core.exceptions import NON_FIELD_ERRORS

from online.models import Offer
from sku.models import Sku


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
        fields = ("first_name_last_name", 'strasse', "hausnummer", "adresszusatz", "zip", "place")
    package_weight = forms.FloatField(label="Paketgewicht in KG", required=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class LabelForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ("tracking_number", "transport_service", "label_pdf")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if isinstance(visible.field, forms.FileField) is False:
                visible.field.widget.attrs["class"] = "form-control"


class AddressForm(forms.ModelForm):
    class Meta:
        model = Adress
        fields = ("first_name_last_name", 'strasse', "hausnummer", "adresszusatz", "zip", "place")
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
    ean_or_sku = forms.CharField(label="EAN/SKU",
                                 help_text="<div class='help-block'>Bitte scannen Sie einen Artikel</div>")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['ean_or_sku'].widget.attrs.update({
            'autofocus': ''
        })
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class BookinForm(forms.Form):
    bookin_amount = forms.IntegerField(required=True, label="Menge")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class ImportForm(forms.Form):
    import_file = forms.FileField(label="Bestellbericht importieren", required=True)


class ConfirmManualForm(forms.Form):
    note = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", "rows": 5}), required=False,
                           label="Bemerkung")


class OnlineSkuForm(forms.ModelForm):
    class Meta:
        model = Sku
        fields = ["sku", "state", "channel", "asin"]

    state = forms.ChoiceField(choices=[("Neu", "Neu"), ("B", "B"), ("C", "C"), ("D", "D"), ("G", "G")])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields["channel"].required = True

        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"

    def clean(self):
        cleaned_data = super().clean()
        sku_query = Sku.objects.filter(sku=cleaned_data.get("sku", ""))
        if sku_query.exclude(sku=self.instance.sku).count() > 0:
            self.add_error("sku", "Diese SKU ist bereits vergeben")

        if cleaned_data.get("sku") != str(self.instance.sku):
            sku_instance = Sku.objects.filter(sku=self.instance.sku).first()
            if sku_instance is not None and (sku_instance.productmission_set.all().count() > 0
                                             or hasattr(sku_instance, "offer") is True):
                self.add_error("sku", "Diese SKU kann nicht geändert werden,"
                                      " da für diese SKU Aufträge oder Angebote bestehen.")
        return cleaned_data


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ["amount"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"
