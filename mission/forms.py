from django import forms
from .models import Mission, ProductMission
from django.forms import modelform_factory, inlineformset_factory, BaseInlineFormSet


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
