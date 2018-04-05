from django import forms
from .models import Order, ProductOrder
from django.forms import modelform_factory, inlineformset_factory, BaseFormSet, BaseInlineFormSet, CharField, FloatField, \
    IntegerField


class OrderForm(forms.ModelForm):
    delivery_date = forms.DateField(input_formats=['%d/%m/%Y'], \
                                    widget=forms.DateTimeInput(format='%d/%m/%Y', attrs={
                                        'class': 'datepicker'
                                    }), label=Order._meta.get_field("delivery_date").verbose_name)

    class Meta:
        model = Order
        fields = ['delivery_date', 'verified', 'supplier']
        widgets = {'delivery_date': forms.DateInput(attrs={"class": "datepicker"})}


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
    ean = forms.CharField(label='EAN', max_length=13)
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


class ProductOrderForm(CommonProductOrderForm):
    pass


class ProductOrderUpdateForm(CommonProductOrderForm):
    #delete = forms.BooleanField(label="Löschen", required=False)
    pass
