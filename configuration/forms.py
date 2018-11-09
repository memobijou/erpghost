from django import forms
from online.models import Channel
from configuration.models import OnlinePositionPrefix
from disposition.models import TransportService, BusinessAccount
from sku.models import Sku


class TransportServiceForm(forms.ModelForm):
    class Meta:
        model = TransportService
        fields = ["name"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"


class BusinessAccountForm(forms.ModelForm):
    class Meta:
        model = BusinessAccount
        fields = ["username", "client", "type"]

    password = forms.CharField(widget=forms.PasswordInput(), label="Passwort")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"


class BusinessAccountFormUpdate(BusinessAccountForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Passwort ändern", required=False)


class OnlinePositionForm(forms.ModelForm):
    class Meta:
        model = OnlinePositionPrefix
        fields = "__all__"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"


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
                                             or sku_instance.offer_set.all().count() > 0):
                self.add_error("sku", "Diese SKU kann nicht geändert werden,"
                                      " da für diese SKU Aufträge oder Angebote bestehen.")
        return cleaned_data
