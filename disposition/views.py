import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render
from django.views import View, generic
from django.core.paginator import Paginator
from disposition.forms import TruckForm, EmployeeForm, ProfileForm, TruckUpdateForm, CreateTruckAppointmentForm
from disposition.models import Employee, Profile, TruckAppointment
from mission.models import DeliveryNote, Truck, Delivery
from django.urls import reverse_lazy
from order.models import Order


class CalendarView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "disposition/calendar.html", self.build_context())

    def build_context(self):
        context = {"title": "Disposition",
                   "deliveries": Delivery.objects.all(),
                   "truck_appointments": TruckAppointment.objects.all(),
                   "orders": Order.objects.all(),
                   }
        return context


class TruckListView(generic.ListView):
    template_name = "disposition/truck_list.html"

    def get_queryset(self):
        queryset = self.filter_queryset_from_request()
        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Disposition LKWs"
        context["fields"] = ["LKW Nummer", "Ankunftstermine"]
        context["filter_fields"] = self.get_filter_fields(Truck)
        return context

    def set_pagination(self, queryset):
        page = self.request.GET.get("page")
        paginator = Paginator(queryset, 15)
        if not page:
            page = 1
        current_page_object = paginator.page(int(page))
        return current_page_object

    def filter_queryset_from_request(self):
        filter_dict = {}
        q_filter = Q()

        for field, verbose_name in self.get_filter_fields():
            if field in self.request.GET:
                GET_value = self.request.GET.get(field)
                if GET_value is not None and GET_value != "":
                    filter_dict[f"{field}__icontains"] = str(self.request.GET.get(field)).strip()

        for item in filter_dict:
            q_filter &= Q(**{item: filter_dict[item]})
        print(q_filter)

        truck_id_exact = self.request.GET.get("truck_id_exact")

        if truck_id_exact is not None and truck_id_exact != "":
            q_filter &= Q(truck_id__icontains=truck_id_exact)

        search_filter = Q()
        search_value = self.request.GET.get("q")

        if search_value is not None and search_value != "":
            search_filter |= Q(truck_id__icontains=search_value)

        q_filter &= search_filter

        queryset = Truck.objects.filter(q_filter).order_by("-id").distinct()
        print(queryset)
        return queryset

    def get_filter_fields(self, exclude=None):
        filter_fields = []
        filter_fields.append(("truck_id", "LKW Nummer"))
        return filter_fields


class TruckUpdateView(generic.UpdateView):
    template_name = "disposition/truck_update_form.html"
    form_class = TruckUpdateForm
    success_url = reverse_lazy("disposition:truck_list")

    def __init__(self, **kwargs):
        self.object = None
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "LKW bearbeiten"
        return context

    def dispatch(self, request, *args, **kwargs):
        self.object = Truck.objects.get(pk=self.kwargs.get("truck_id"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.object


class TruckAppointmentCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = "disposition/form.html"
    login_url = "/login/"
    form_class = CreateTruckAppointmentForm
    success_url = reverse_lazy("disposition:truck_list")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Disposition anlegen"
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        self.set_time(instance)
        self.create_new_truck(instance)
        instance.save()
        self.set_outgoing_incoming(instance)
        instance.truck.save()
        return super().form_valid(form)

    def set_outgoing_incoming(self, instance):
        outgoing = self.request.POST.get("outgoing")
        print(f"whattttt 222: {outgoing}")
        instance.truck.outgoing = outgoing
        print(f"222: {instance.truck.outgoing}")

    def create_new_truck(self, instance):
        new_truck = Truck.objects.create()
        instance.truck = new_truck

    def set_time(self, instance):
        hour_start = self.request.POST.get("hour_start")
        minute_start = self.request.POST.get("minute_start")
        start_time = datetime.time(hour=int(hour_start), minute=int(minute_start))
        hour_end = self.request.POST.get("hour_end")
        minute_end = self.request.POST.get("minute_end")
        end_time = datetime.time(hour=int(hour_end), minute=int(minute_end))
        instance.arrival_time_start = start_time
        instance.arrival_time_end = end_time


class TruckAppointmentUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "disposition/form.html"
    login_url = "/login/"
    form_class = TruckForm
    success_url = reverse_lazy("disposition:truck_list")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.appointment = None

    def dispatch(self, request, *args, **kwargs):
        self.appointment = TruckAppointment.objects.filter(pk=self.kwargs.get("appointment_id")).first()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Disposition bearbeiten"
        context["truck_id"] = self.appointment.truck.pk
        return context

    def get_form(self, form_class=None):
        form = super().get_form()

        if self.appointment.arrival_time_start is not None:
            form.initial["hour_start"] = ("%02d" % (self.appointment.arrival_time_start.hour,),
                                          "%02d" % (self.appointment.arrival_time_start.hour,))
            form.initial["minute_start"] = ("%02d" % (self.appointment.arrival_time_start.minute,),
                                            "%02d" % (self.appointment.arrival_time_start.minute,))

        if self.appointment.arrival_time_end is not None:
            form.initial["hour_end"] = ("%02d" % (self.appointment.arrival_time_end.hour,),
                                        "%02d" % (self.appointment.arrival_time_end.hour,))
            form.initial["minute_end"] = ("%02d" % (self.appointment.arrival_time_end.minute,),
                                          "%02d" % (self.appointment.arrival_time_end.minute,)
                                          )
        return form

    def get_object(self, queryset=None):
        return self.appointment

    def form_valid(self, form):
        instance = form.save(commit=False)
        self.set_time(instance)
        instance.save()
        return super().form_valid(form)

    def set_time(self, instance):
        hour_start = int(self.request.POST.get("hour_start"))
        minute_start = int(self.request.POST.get("minute_start"))
        start_time = datetime.time(hour=hour_start, minute=minute_start)
        instance.arrival_time_start = start_time

        hour_end = int(self.request.POST.get("hour_end"))
        minute_end = int(self.request.POST.get("minute_end"))
        end_time = datetime.time(hour=hour_end, minute=minute_end)
        instance.arrival_time_end = end_time


class AppointmentToTruckView(TruckAppointmentCreateView):
    form_class = TruckForm

    def create_new_truck(self, instance):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["truck_id"] = Truck.objects.get(id=self.kwargs.get("truck_id")).pk
        context["title"] = "Disposition"
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.truck_id = self.kwargs.get("truck_id")
        instance.save()
        return super().form_valid(form)


class EmployeeListView(generic.ListView):
    template_name = "disposition/employee/employee_list.html"

    def get_queryset(self):
        queryset = Employee.objects.all()
        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Mitarbeiter"
        context["fields"] = ["Bild", "Vorname", "Nachname", "Benutzername"]
        return context

    def set_pagination(self, queryset):
        page = self.request.GET.get("page")
        paginator = Paginator(queryset, 15)
        if not page:
            page = 1
        current_page_object = paginator.page(int(page))
        return current_page_object


class EmployeeCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = "disposition/employee/form.html"
    login_url = "/login/"
    form_class = EmployeeForm
    success_url = reverse_lazy("disposition:employee_list")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Mitarbeiter anlegen"
        return context


class EmployeeUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "disposition/employee/form.html"
    login_url = "/login/"
    form_class = EmployeeForm
    success_url = reverse_lazy("disposition:employee_list")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = None

    def dispatch(self, request, *args, **kwargs):
        self.employee = Employee.objects.filter(id=self.kwargs.get("employee_id")).first()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Mitarbeiter bearbeiten"
        context["employee"] = self.employee
        context["profile_form"] = self.get_profile_form()
        return context

    def get_profile_form(self):
        if self.request.method == "POST":
            return ProfileForm(data=self.request.POST, files=self.request.FILES,
                               instance=self.employee.user.profile)
        else:
            if hasattr(self.employee.user, "profile"):
                return ProfileForm(instance=self.employee.user.profile)
            return ProfileForm()

    def form_valid(self, form, **kwargs):
        profile_form = self.get_profile_form()

        if profile_form.is_valid() is True:
            try:
                if self.request.FILES.get("profile_image") is not None\
                        and self.request.FILES.get("profile_image") != "":
                    self.employee.user.profile.profile_image = self.request.FILES.get("profile_image")
            except Profile.DoesNotExist:
                profile = Profile()
                profile.save()
                self.employee.user.profile = profile
                self.employee.user.save()
                self.employee.user.profile.profile_image = self.request.FILES.get("profile_image")
            self.employee.user.profile.save()
            return super().form_valid(form)
        else:
            return render(self.request, self.template_name, self.get_context_data(**kwargs))

    def get_object(self, queryset=None):
        return self.employee
