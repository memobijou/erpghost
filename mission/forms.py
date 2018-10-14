from django import forms
from django.db.models import Q
from django.forms import inlineformset_factory, BaseInlineFormSet, CharField, FloatField, IntegerField

from product.models import Product
from .models import Mission, ProductMission, Billing, PartialMissionProduct


class MissionForm(forms.ModelForm):
    delivery_date = forms.DateField(input_formats=['%d/%m/%Y'],
                                    widget=forms.DateTimeInput(format='%d/%m/%Y', attrs={
                                        'class': 'datepicker'
                                    }), label=Mission._meta.get_field("delivery_date").verbose_name)

    # delivery_address = forms.ModelChoiceField(queryset=Adress.objects.filter(), label="Lieferadresse", required=False)

    class Meta:
        model = Mission
        fields = ['delivery_date', 'terms_of_delivery', 'terms_of_payment', "customer",
                  'customer_order_number', ]
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

    state = forms.ChoiceField(label="Zustand", choices=((None, "----"), ("Neu", "Neu"), ("B", "B"),
                                                        ("C", "C"), ("D", "D"), ("G", "G")), required=False)
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


class ProductMissionForm(CommonProductMissionForm):
    pass


class ProductMissionUpdateForm(CommonProductMissionForm):
    delete = forms.CharField(max_length=100, widget=forms.HiddenInput(), required=False)

    def __init__(self, **kwargs):
        self.product_mission = kwargs.pop("product_mission")
        super().__init__(**kwargs)

    def clean_amount(self):
        data = self.cleaned_data.get("amount")
        sum_all_amounts = 0

        if self.product_mission is None:
            return data

        for goods_issue_delivery_mission_product in PartialMissionProduct.objects.\
                filter(product_mission=self.product_mission):

            sum_all_amounts += goods_issue_delivery_mission_product.amount

        if self.cleaned_data.get('amount') < sum_all_amounts:
            self.data["amount"] = self.product_mission.amount
            raise forms.ValidationError(f"Die Menge darf nicht kleiner als {sum_all_amounts} sein.")
        return data

DATE_INPUT_FORMATS = ['%d/%m/%Y', "%d.%m.%Y"]


class BillingForm(forms.ModelForm):

    class Meta:
        model = Billing
        fields = ("transport_service", "shipping_number_of_pieces", "shipping_costs")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class DeliveryForm(forms.Form):
    delivery_date = forms.DateField(required=False, label="Lieferdatum", input_formats=DATE_INPUT_FORMATS)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            if type(visible.field) is forms.DateField:
                visible.field.widget.attrs["class"] += " datepicker"
                visible.field.widget.attrs["readonly"] = ""
                visible.field.widget.attrs["style"] = "background-color:white;"
                visible.field.widget.attrs["placeholder"] = "Falls abweichend von Auftragslieferdatum"


class PickForm(forms.Form):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
                visible.field.widget.attrs["class"] = "form-control"


