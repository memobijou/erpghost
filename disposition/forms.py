from django.forms import ModelForm
from django.utils.safestring import mark_safe

from disposition.models import Employee, Profile, TruckAppointment
from django.contrib.admin import widgets
from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from django.forms import inlineformset_factory
from django.contrib.auth.models import User

from mission.models import Truck

hours = [(None, "----")]
hours += [("%02d" % (hour,), ("%02d" % (hour,))) for hour in range(0, 24)]

minutes = [(None, "----")]
minutes += [("%02d" % (minute,), ("%02d" % (minute,))) for minute in range(0, 60)]
DATE_INPUT_FORMATS = ['%d/%m/%Y', "%d.%m.%Y"]

INCOMING_OUTGOING = ((True, "Ausgang"), (False, "Eingang"))


class CustomChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        label_html = f"{obj}"
        if obj.user and obj.user.profile and obj.user.profile.profile_image:
            return mark_safe(f""
                             f"<div class='col-md-12'>"
                             f"<img src='%s' class='img-responsive' style='max-height:80px;cursor:pointer'/>"
                             f"</div><br/>"
                             f"<div class='col-md-8'>"
                             f"{obj}"
                             f"</div>"
                             % obj.user.profile.profile_image.url)
        return mark_safe(f"{label_html}")


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
        print(f"aadsfdsafsd: {type(self.fields['employees'])}")
        self.fields["employees"] = CustomChoiceField(queryset=Employee.objects.all(),  widget=CheckboxSelectMultiple())

        for visible in self.visible_fields():
            if type(visible.field) is not forms.BooleanField and type(visible.field) is not CustomChoiceField:
                visible.field.widget.attrs["class"] = "form-control"
        self.fields["arrival_date"].widget.attrs["class"] += " datepicker"
        self.fields["arrival_date"].input_formats = DATE_INPUT_FORMATS


class CreateTruckAppointmentForm(TruckForm):
    outgoing = forms.ChoiceField(choices=INCOMING_OUTGOING)


class TruckUpdateForm(forms.ModelForm):
    class Meta:
        model = Truck
        fields = ["outgoing"]

    outgoing = forms.ChoiceField(choices=INCOMING_OUTGOING, label="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


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
        fields = ["first_name", "last_name", "profile_image"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is not forms.ImageField:
                visible.field.widget.attrs["class"] = "form-control"
