from django.http import HttpResponseRedirect
from django.shortcuts import render

from mission.models import Mission
from django.views.generic import UpdateView
from django.urls import reverse_lazy

from online.dpd import DPDLabelCreator
from online.forms import DPDForm, LabelForm
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from online.forms import AddressForm


class CreateLabelView(LoginRequiredMixin, View):
    template_name = "online/label/form.html"
    form_class = DPDForm

    def __init__(self, **kwargs):
        self.transport_account = None
        self.mission = None
        self.context = None
        self.label_form = None
        self.address_form = None
        super().__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.mission = Mission.objects.get(pk=self.kwargs.get("pk"))
        self.label_form = self.get_label_form()
        self.address_form = self.get_address_form()
        self.context = self.get_context()
        return super().dispatch(request, *args, **kwargs)

    def get_label_form(self):
        if self.request.method == "POST":
            self.label_form = LabelForm(data=self.request.POST, files=self.request.FILES)
        else:
            self.label_form = LabelForm()
        return self.label_form

    def get_address_form(self):
        if self.request.method == "POST":
            self.address_form = AddressForm(data=self.request.POST)
        else:
            self.address_form = AddressForm(instance=self.mission.delivery_address)
        return self.address_form

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        if self.request.POST.get("action") == "standard":
            if self.label_form.is_valid() is True:
                instance = self.label_form.save(commit=False)
                instance.mission = self.mission
                instance.save()
            else:
                return render(request, self.template_name, self.context)
            return HttpResponseRedirect(self.get_success_url())
        elif self.request.POST.get("action") == "dpd_api":
            dpd_creator = DPDLabelCreator(multiple_missions=[self.mission])
            dpd_creator.create_label()
            return HttpResponseRedirect(self.get_success_url())

    def get_context(self):
        return {"title": "Paketlabel erstellen", "mission": self.mission,
                "label_form": self.label_form, "address_form": self.address_form
                }

    def get_success_url(self):
        if self.request.GET.get("not_packing") is not None:
            if self.request.GET.get("is_export") is not None:
                return reverse_lazy("online:export") + "?" + self.request.GET.urlencode()
            else:
                return reverse_lazy("online:list")
        return reverse_lazy("online:packing", kwargs={"pk": self.mission.online_picklist.pk})

    def form_valid(self, form, **kwargs):
        dpd_label_creator = DPDLabelCreator(multiple_missions=[self.mission], ignore_pickorder=True)
        parcel_label_numbers, message = dpd_label_creator.create_label()
        print(f"hey {message} --- {type(message)}")
        if message is not None and message != "":
            form.add_error(None, message)
            return super().form_invalid(form)
        return super().form_valid(form)