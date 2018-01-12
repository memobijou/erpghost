from django import forms
from .models import Order, ProductOrder
from django.forms import modelform_factory, inlineformset_factory


class OrderForm(forms.ModelForm):
	delivery_date = forms.DateField(input_formats=['%d/%m/%Y'],\
				     widget=forms.DateTimeInput(format='%d/%m/%Y', attrs={
            			'class': 'datepicker'
    }))

	class Meta:
		model = Order
		fields = ['ordernumber', 'delivery_date', 'status']
		widgets={'deliver	y_date': forms.DateInput(attrs={"class": "datepicker"})}

# inline_order = modelform_factory(Order, exclude=('id', 'products'),\
# 				 widgets={'delivery_date': forms.DateInput(attrs={"class": "datepicker"})})


ProductOrderFormsetInline = inlineformset_factory(Order, ProductOrder, can_delete=True, extra=0, exclude=["id"])
