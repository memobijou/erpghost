from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
	delivery_date = forms.DateField(input_formats=['%d/%m/%Y'], widget=forms.TextInput(attrs={'class': 'datepicker'}))

	class Meta:
		model = Order
		exclude = ['id', 'products']
		widgets={'delivery_date': forms.DateInput(attrs={"class": "datepicker"})}

# inline_order = modelform_factory(Order, exclude=('id', 'products'),\
# 				 widgets={'delivery_date': forms.DateInput(attrs={"class": "datepicker"})})
