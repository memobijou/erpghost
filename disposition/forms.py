from django.forms import ModelForm
from mission.models import Truck
from disposition.models import Employee, Profile
from django.contrib.admin import widgets
from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from django.forms import inlineformset_factory
from django.contrib.auth.models import User


hours = [(hour, hour) for hour in range(0, 24)]
minutes = [(minute, minute) for minute in range(0, 60)]
DATE_INPUT_FORMATS = ['%d/%m/%Y', "%d.%m.%Y"]


class TruckForm(ModelForm):
    class Meta:
        model = Truck
        fields = ["arrival_date", "employees"]

    hour = forms.ChoiceField(label="Stunde", choices=hours)
    minute = forms.ChoiceField(label="Minute", choices=minutes)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        self.fields["arrival_date"].widget.attrs["class"] += " datepicker"
        self.fields["arrival_date"].input_formats = DATE_INPUT_FORMATS
        self.fields["employees"].widget = CheckboxSelectMultiple()
        self.fields["employees"].queryset = Employee.objects.all()


class EmployeeForm(ModelForm):
    class Meta:
        model = Employee
        fields = ["user"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ["profile_image"]

