from django import forms
from .models import Mission, ProductMission
from django.forms import modelform_factory, inlineformset_factory


class MissionForm(forms.ModelForm):
	delivery_date = forms.DateField(input_formats=['%d/%m/%Y'],\
				     widget=forms.DateTimeInput(format='%d/%m/%Y', attrs={
            			'class': 'datepicker'
    }))

	class Meta:
		model = Mission
		fields = ['mission_number', 'delivery_date', 'status']
		widgets={'delivery_date': forms.DateInput(attrs={"class": "datepicker"})}

ProductMissionFormsetInline = inlineformset_factory(Mission, ProductMission, can_delete=True, extra=1, exclude=["id"])
