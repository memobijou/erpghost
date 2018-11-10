from django import forms

from configuration.models import OnlinePositionPrefix
from disposition.models import TransportService, BusinessAccount


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


