from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from utils.utils import get_field_names, get_queries_as_json, set_field_names_onview, set_paginated_queryset_onview, \
    filter_queryset_from_request, get_query_as_json, get_related_as_json, get_relation_fields, set_object_ondetailview
from mission.models import Mission, ProductMission
from mission.forms import MissionForm, ProductMissionFormsetInline
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import inlineformset_factory, modelform_factory


# Create your views here.

class MissionDetailView(DetailView):

    def get_object(self):
        obj = get_object_or_404(Mission, pk=self.kwargs.get("pk"))
        return obj

    def get_context_data(self, *args, **kwargs):
        context = super(MissionDetailView, self).get_context_data(*args, **kwargs)
        context["title"] = "Auftrag " + context["object"].mission_number
        set_object_ondetailview(context=context, ModelClass=Mission, exclude_fields=["id"], \
                                exclude_relations=[], exclude_relation_fields={"products": ["id"]})
        return context


class MissionListView(ListView):
    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Mission)
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(MissionListView, self).get_context_data(*args, **kwargs)
        context["title"] = "Auftrag"

        set_field_names_onview(queryset=context["object_list"], context=context, ModelClass=Mission, \
                               exclude_fields=["id", "verified", "pickable"],
                               exclude_filter_fields=["id", "verified", "pickable"])

        if context["object_list"].count() > 0:
            set_paginated_queryset_onview(context["object_list"], self.request, 15, context)

        context["option_fields"] = [
            {"status": ["WARENAUSGANG", "AKZEPTIERT", "ABGELEHNT", "PICKBEREIT", "AUSSTEHEND", "OFFEN", "VERSANDBEREIT"]}]
        return context


class MissionCreateView(CreateView):
    template_name = "mission/form.html"
    form_class = MissionForm

    def get_context_data(self, *args, **kwargs):
        context = super(MissionCreateView, self).get_context_data(*args, **kwargs)
        context["title"] = "Auftrag anlegen"
        context["matching_"] = "Product"  # Hier Modelname übergbenen
        formset_class = inlineformset_factory(Mission, ProductMission, can_delete=False, extra=3,
                                              exclude=["id", "missing_amount", "confirmed"])

        if self.request.POST:
            formset = formset_class(self.request.POST, self.request.FILES, instance=self.object)
        else:
            formset = formset_class(instance=self.object)

        context["formset"] = formset

        return context

    def form_valid(self, form, *args, **kwargs):
        self.object = form.save()

        context = self.get_context_data(*args, **kwargs)
        formset = context["formset"]

        if formset.is_valid():
            formset.save()
        else:
            return render(self.request, self.template_name, context)

        return HttpResponseRedirect(self.get_success_url())


class MissionUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "mission/form.html"
    login_url = "/login/"
    form_class = MissionForm

    def get_object(self):
        object = Mission.objects.get(id=self.kwargs.get("pk"))
        return object

    def dispatch(self, request, *args, **kwargs):
        # request.user = AnonymousUser()
        return super(MissionUpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(MissionUpdateView, self).get_context_data(*args, **kwargs)
        context["title"] = f"Auftrag {self.object.mission_number} bearbeiten"
        context["matching_"] = "Product"  # Hier Modelname übergbenen
        if self.request.POST:
            formset = ProductMissionFormsetInline(self.request.POST, self.request.FILES, instance=self.object)
        else:
            formset = ProductMissionFormsetInline(instance=self.object)
        context["formset"] = formset
        return context

    def form_valid(self, form, *args, **kwargs):
        self.object = form.save()
        context = self.get_context_data(*args, **kwargs)
        formset = context["formset"]

        if formset.is_valid():
            formset.save()
        else:
            return render(self.request, self.template_name, context)

        return HttpResponseRedirect(self.get_success_url())


class ScanMissionTemplateView(UpdateView):
    template_name = "mission/scan_mission.html"
    form_class = modelform_factory(ProductMission, fields=("confirmed",))

    def get_object(self, *args, **kwargs):
        object = Mission.objects.get(pk=self.kwargs.get("pk"))
        return object

    def get_context_data(self, *args, **kwargs):
        context = super(ScanMissionTemplateView, self).get_context_data(*args, **kwargs)
        context["object"] = self.get_object(*args, **kwargs)

        product_missions = context["object"].productmission_set.all()

        context["product_missions"] = product_missions

        if product_missions.count() > 0:

            set_field_names_onview(queryset=context["object"], context=context, ModelClass=Mission,
                                   exclude_fields=["id"], exclude_filter_fields=["id"])

            set_field_names_onview(queryset=product_missions, context=context, ModelClass=ProductMission,
                                   exclude_fields=["id", "mission"], exclude_filter_fields=["id", "mission"],
                                   template_tagname="product_mission_field_names",
                                   allow_related=True)
        else:
            context["product_missions"] = None

        return context

    def form_valid(self, form, *args, **kwargs):
        object = form.save()
        confirmed_bool = self.request.POST.get("confirmed")
        product_id = self.request.POST.get("product_id")
        missing_amount = self.request.POST.get("missing_amount")

        for product_mission in object.productmission_set.all():

            if str(product_mission.pk) == str(product_id):
                product_mission.confirmed = confirmed_bool
                product_mission.save()

            if str(product_mission.pk) == str(product_id):
                if confirmed_bool == "0":
                    product_mission.missing_amount = missing_amount
                elif confirmed_bool == "1":
                    product_mission.missing_amount = None
                product_mission.confirmed = confirmed_bool
                product_mission.save()
        return HttpResponseRedirect("")
