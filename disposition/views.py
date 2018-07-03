import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View, generic
from django.core.paginator import Paginator
from disposition.forms import TruckForm, EmployeeForm, ProfileForm
from disposition.models import Employee, Profile
from mission.models import DeliveryNote, Truck
from django.urls import reverse_lazy


class CalendarView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "disposition/calendar.html", self.build_context())

    def build_context(self):
        context = {"title": "Disposition",
                   "delivery_notes": DeliveryNote.objects.all()}
        return context


class TruckListView(generic.ListView):
    template_name = "disposition/truck_list.html"

    def get_queryset(self):
        queryset = DeliveryNote.objects.all()
        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Disposition"
        context["fields"] = ["Lieferscheinnummer", "Lieferdatum", "LKW buchen"]
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
        self.delivery_note = None

    def dispatch(self, request, *args, **kwargs):
        self.delivery_note = DeliveryNote.objects.\
            filter(delivery_note_number=self.kwargs.get("delivery_note_number")).first()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Disposition anlegen"
        context["delivery_note"] = self.delivery_note
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance = self.save_time(instance)
        instance.delivery_note = self.delivery_note
        instance.save()
        return super().form_valid(form)

    def save_time(self, instance):
        hour = self.request.POST.get("hour")
        minute = self.request.POST.get("minute")
        time = datetime.time(hour=int(hour), minute=int(minute))
        instance.arrival_time = time
        return instance


class TruckUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "disposition/form.html"
    login_url = "/login/"
    form_class = TruckForm
    success_url = reverse_lazy("disposition:truck_list")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.truck = None
        self.delivery_note = None

    def dispatch(self, request, *args, **kwargs):
        self.truck = Truck.objects.filter(id=self.kwargs.get("truck_id")).first()
        self.delivery_note = DeliveryNote.objects.\
            filter(delivery_note_number=self.truck.delivery_note.delivery_note_number).first()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Disposition bearbeiten"
        context["delivery_note"] = self.delivery_note
        return context

    def get_form(self, form_class=None):
        form = super().get_form()
        form.initial["hour"] = (self.truck.arrival_time.hour, self.truck.arrival_time.hour)
        form.initial["minute"] = (self.truck.arrival_time.minute, self.truck.arrival_time.minute)
        return form

    def get_object(self, queryset=None):
        return self.truck

    def form_valid(self, form):
        return super().form_valid(form)

    def save_time(self):
        hour = self.request.POST.get("hour")
        minute = self.request.POST.get("minute")
        datetime.time(hour=hour, minute=minute)


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
