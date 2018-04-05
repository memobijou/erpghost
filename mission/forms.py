from django import forms
from .models import Mission, ProductMission
from django.forms import modelform_factory, inlineformset_factory, BaseInlineFormSet, CharField, FloatField, \
    IntegerField


class MissionForm(forms.ModelForm):
    delivery_date = forms.DateField(input_formats=['%d/%m/%Y'],
                                    widget=forms.DateTimeInput(format='%d/%m/%Y', attrs={
                                        'class': 'datepicker'
                                    }), label=Mission._meta.get_field("delivery_date").verbose_name)

    class Meta:
        model = Mission
        fields = ['delivery_date', 'pickable', "customer"]
        widgets = {'delivery_date': forms.DateInput(attrs={"class": "datepicker"})}


class BaseProductMissionFormset(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields["product"].label = "Artikel"
        form.fields["amount"].label = "Menge"
        form.fields["amount"].initial = ""

ProductMissionFormsetUpdate = inlineformset_factory(Mission, ProductMission, can_delete=True, extra=1,
                                                    exclude=["id", "missing_amount", "confirmed"], formset=BaseProductMissionFormset)

ProductMissionFormsetCreate = inlineformset_factory(Mission, ProductMission, can_delete=False, extra=3,
                                              exclude=["id", "missing_amount", "confirmed"], formset=BaseProductMissionFormset)


class CommonProductMissionForm(forms.Form):
    ean = forms.CharField(label='EAN', max_length=50)
    amount = forms.IntegerField(label='Menge')
    netto_price = forms.FloatField(label="Einzelpreis (Netto)")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField:
                visible.field.widget.attrs["class"] = "form-control"

    class Meta:
        abstract = True


class ProductMissionForm(CommonProductMissionForm):
    pass


class ProductMissionUpdateForm(CommonProductMissionForm):
    # delete = forms.BooleanField(label="Löschen", required=False)
    pass
