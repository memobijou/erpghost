import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View, generic
from django.core.paginator import Paginator
from disposition.forms import TruckForm, EmployeeForm, ProfileForm
from disposition.models import Employee, Profile, TruckAppointment
from mission.models import DeliveryNote, Truck, Delivery
from django.urls import reverse_lazy


class CalendarView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "disposition/calendar.html", self.build_context())

    def build_context(self):
        context = {"title": "Disposition",
                   "deliveries": Delivery.objects.all(),
                   "truck_appointments": TruckAppointment.objects.all()}
        return context


class TruckListView(generic.ListView):
    template_name = "disposition/truck_list.html"

    def get_queryset(self):
        queryset = Truck.objects.all()
        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Disposition LKWs"
        context["fields"] = ["LKW Nummer", "Ankunftstermine"]
        return context

    def set_pagination(self, queryset):
        page = self.request.GET.get("page")
        paginator = Paginator(queryset, 15)
        if not page:
            page = 1
        current_page_object = paginator.page(int(page))
        return current_page_object


class TruckCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = "disposition/form.html"
    login_url = "/login/"
    form_class = TruckForm
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
        return super().form_valid(form)

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


class TruckUpdateView(LoginRequiredMixin, generic.UpdateView):
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
            form.initial["hour_start"] = (self.appointment.arrival_time_start.hour, self.appointment.arrival_time_start.hour)
            form.initial["minute_start"] = (self.appointment.arrival_time_start.minute, self.appointment.arrival_time_start.minute)

        if self.appointment.arrival_time_end is not None:
            form.initial["hour_end"] = (self.appointment.arrival_time_end.hour, self.appointment.arrival_time_end.hour)
            form.initial["minute_end"] = (self.appointment.arrival_time_end.minute, self.appointment.arrival_time_end.minute)
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


class AppointmentToTruckView(TruckCreateView):
    def create_new_truck(self, instance):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["truck_id"] = Truck.objects.get(id=self.kwargs.get("truck_id")).pk
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
        context["fields"] = ["Mitarbeiter"]
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
            print(self.request.FILES)
            return ProfileForm(data=self.request.POST, files=self.request.FILES)
        else:
            if hasattr(self.employee.user, "profile"):
                self.request.FILES["profile_image"] = self.employee.user.profile.profile_image
                return ProfileForm(files=self.request.FILES)
            return ProfileForm()

    def form_valid(self, form, **kwargs):
        profile_form = self.get_profile_form()

        if profile_form.is_valid() is True:
            try:
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
