from django import forms
from product.models import Product
from .models import Mission, ProductMission
from django.forms import modelform_factory, inlineformset_factory, BaseInlineFormSet, CharField, FloatField, \
    IntegerField
from client.models import Client
from adress.models import Adress
from django.core.validators import MinValueValidator


class MissionForm(forms.ModelForm):
    delivery_date = forms.DateField(input_formats=['%d/%m/%Y'],
                                    widget=forms.DateTimeInput(format='%d/%m/%Y', attrs={
                                        'class': 'datepicker'
                                    }), label=Mission._meta.get_field("delivery_date").verbose_name)

    # delivery_address = forms.ModelChoiceField(queryset=Adress.objects.filter(), label="Lieferadresse", required=False)

    class Meta:
        model = Mission
        fields = ['delivery_date', 'confirmed', 'terms_of_delivery', 'terms_of_payment', "customer",
                  'customer_order_number', 'shipping', 'shipping_number_of_pieces', 'shipping_costs']
        widgets = {'delivery_date': forms.DateInput(attrs={"class": "datepicker"})}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"
            if type(visible.field) is forms.DateField:
                visible.field.widget.attrs["class"] = "form-control datepicker"


class BaseProductMissionFormset(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields["product"].label = "Artikel"
        form.fields["amount"].label = "Menge"
        form.fields["amount"].initial = ""

ProductMissionFormsetUpdate = inlineformset_factory(Mission, ProductMission, can_delete=True, extra=1,
                                                    exclude=["id", "missing_amount", "confirmed"],
                                                    formset=BaseProductMissionFormset)

ProductMissionFormsetCreate = inlineformset_factory(Mission, ProductMission, can_delete=False, extra=3,
                                                    exclude=["id", "missing_amount", "confirmed"],
                                                    formset=BaseProductMissionFormset)


class CommonProductMissionForm(forms.Form):
    ean = forms.CharField(label='EAN', max_length=50)
    amount = forms.IntegerField(label='Menge', min_value=1)
    netto_price = forms.FloatField(label="Einzelpreis (Netto)", min_value=0.1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField:
                visible.field.widget.attrs["class"] = "form-control"

    def clean_ean(self):
        data = self.cleaned_data['ean'].strip()
        if Product.objects.filter(ean__iexact=data).count() == 0:
            raise forms.ValidationError("Sie müssen eine gültige EAN eingeben!")

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return data

    class Meta:
        abstract = True


class ProductMissionForm(CommonProductMissionForm):
    pass


class ProductMissionUpdateForm(CommonProductMissionForm):
    # delete = forms.BooleanField(label="Löschen", required=False)
    pass
