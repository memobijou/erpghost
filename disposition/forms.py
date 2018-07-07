from django.forms import ModelForm
from disposition.models import Employee, Profile, TruckAppointment
from django.contrib.admin import widgets
from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from django.forms import inlineformset_factory
from django.contrib.auth.models import User

hours = [(None, "----")]
hours += [("%02d" % (hour,), ("%02d" % (hour,))) for hour in range(0, 24)]

minutes = [(None, "----")]
minutes += [("%02d" % (minute,), ("%02d" % (minute,))) for minute in range(0, 60)]
DATE_INPUT_FORMATS = ['%d/%m/%Y', "%d.%m.%Y"]


class TruckForm(ModelForm):
    class Meta:
        model = TruckAppointment
        fields = ["arrival_date", "employees"]

    hour_start = forms.ChoiceField(label="Stunde von", choices=hours, required=True)
    minute_start = forms.ChoiceField(label="Minute von", choices=minutes, required=True)

    hour_end = forms.ChoiceField(label="Stunde bis", choices=hours, required=True)
    minute_end = forms.ChoiceField(label="Minute bis", choices=minutes, required=True)

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

