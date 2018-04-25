from django import forms

from adress.models import Adress
from product.models import Product
from .models import Order, ProductOrder
from django.forms import modelform_factory, inlineformset_factory, BaseFormSet, BaseInlineFormSet, CharField, FloatField, \
    IntegerField


class OrderForm(forms.ModelForm):
    delivery_date = forms.DateField(input_formats=['%d/%m/%Y'], \
                                    widget=forms.DateTimeInput(format='%d/%m/%Y', attrs={
                                        'class': 'datepicker'
                                    }), label=Order._meta.get_field("delivery_date").verbose_name)

    delivery_address = forms.ModelChoiceField(queryset=Adress.objects.filter(contact__client__isnull=False),
                                              label="Lieferadresse")

    class Meta:
        model = Order
        fields = ['delivery_date', 'verified', 'supplier', "terms_of_payment", "terms_of_delivery", 'delivery_address']
        widgets = {'delivery_date': forms.DateInput(attrs={"class": "datepicker"})}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"
            if type(visible.field) is forms.DateField:
                visible.field.widget.attrs["class"] = "form-control datepicker"


class BaseProductOrderFormset(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields["product"].label = "Artikel"
        form.fields["amount"].label = "Menge"
        form.fields["amount"].initial = ""


ProductOrderFormsetUpdate = inlineformset_factory(Order, ProductOrder, can_delete=True, extra=1,
                                                  exclude=["id", "missing_amount", "confirmed"],
                                                  formset=BaseProductOrderFormset)

ProductOrderFormsetCreate = inlineformset_factory(Order, ProductOrder, extra=3,
                                                  exclude=["id", "missing_amount", "confirmed"],
                                                  formset=BaseProductOrderFormset)


class CommonProductOrderForm(forms.Form):
    ean = forms.CharField(label='EAN', max_length=200)
    amount = forms.IntegerField(label='Menge')
    netto_price = forms.FloatField(label="Einzelpreis (Netto)")

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


class ProductOrderForm(CommonProductOrderForm):
    pass


class ProductOrderUpdateForm(CommonProductOrderForm):
    #delete = forms.BooleanField(label="Löschen", required=False)
    pass
