from django import forms
from .models import Order, ProductOrder
from django.forms import modelform_factory, inlineformset_factory, BaseFormSet, BaseInlineFormSet


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
                                                    exclude=["id", "missing_amount", "confirmed"], formset=BaseProductOrderFormset)

ProductOrderFormsetCreate = inlineformset_factory(Order, ProductOrder, can_delete=False, extra=3,
                                              exclude=["id", "missing_amount", "confirmed"], formset=BaseProductOrderFormset)



