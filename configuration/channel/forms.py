from django import forms
from online.models import Channel


class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ["name", "market", "client"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"
