from django import forms
from django.db.models import Q

from adress.models import Adress
from client.models import Client
from product.models import Product
from .models import Order, ProductOrder
from django.forms import modelform_factory, inlineformset_factory, BaseFormSet, BaseInlineFormSet, CharField, FloatField, \
    IntegerField
from django.core.validators import MinValueValidator


class OrderForm(forms.ModelForm):
    delivery_date = forms.DateField(input_formats=['%d/%m/%Y'], \
                                    widget=forms.DateTimeInput(format='%d/%m/%Y', attrs={
                                        'class': 'datepicker'
                                    }), label=Order._meta.get_field("delivery_date").verbose_name)


    # for client in Client.objects.all():
    #     if client.contact.delivery_address is not None:
    #         client_delivery_addresses_ids.append(client.contact.delivery_address.pk)
    #
    # delivery_address = forms.ModelChoiceField(queryset=Adress.objects.filter(pk__in=client_delivery_addresses_ids),
    #                                           label="Lieferadresse", required=False)

    class Meta:
        model = Order
        fields = ['delivery_date', 'verified', 'supplier', "terms_of_payment", "terms_of_delivery", 'delivery_address',
                  'shipping', 'shipping_number_of_pieces', 'shipping_costs']
        widgets = {'delivery_date': forms.DateInput(attrs={"class": "datepicker"})}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        client_delivery_addresses_ids = []

        for client in Client.objects.all():
            if client.contact.delivery_address is not None:
                client_delivery_addresses_ids.append(client.contact.delivery_address.pk)

        self.fields["delivery_address"] = forms.\
            ModelChoiceField(queryset=Adress.objects.filter(pk__in=client_delivery_addresses_ids),
                             label="Lieferadresse", required=False)

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
    state = forms.ChoiceField(label="Zustand", choices=((None, "----"), ("Neu", "Neu"), ("A", "A"), ("B", "B"),
                                                        ("C", "C"), ("D", "D")), required=False)
    amount = forms.IntegerField(label='Menge', min_value=1)
    netto_price = forms.FloatField(label="Einzelpreis (Netto)", min_value=0.1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField or type(visible.field) is forms.ChoiceField:
                visible.field.widget.attrs["class"] = "form-control"

    def clean_ean(self):
        data = self.cleaned_data['ean'].strip()
        if Product.objects.filter(Q(ean__iexact=data) | Q(sku__sku=data)).count() == 0:
            raise forms.ValidationError("Sie müssen eine gültige EAN oder SKU eingeben!")

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return data

    class Meta:
        abstract = True


class ProductOrderForm(CommonProductOrderForm):
    pass


class ProductOrderUpdateForm(CommonProductOrderForm):
    delete = forms.CharField(max_length=100, widget=forms.HiddenInput(), required=False)
