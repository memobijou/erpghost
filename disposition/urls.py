from django.conf.urls import url

from disposition.views import CalendarView, TruckAppointmentUpdateView, TruckListView, TruckAppointmentCreateView, \
    EmployeeListView, EmployeeCreateView, EmployeeUpdateView, AppointmentToTruckView, TruckUpdateView

urlpatterns = [
    url(r'^$', CalendarView.as_view(), name="calendar"),
    url(r'^edit/(?P<appointment_id>\d+)/$', TruckAppointmentUpdateView.as_view(), name="appointment_edit"),
    url(r'^trucks/$', TruckListView.as_view(), name="truck_list"),
    url(r'^create/$', TruckAppointmentCreateView.as_view(), name="truck_create"),
    url(r'^create/(?P<truck_id>\d+)/$', AppointmentToTruckView.as_view(), name="appointment_to_truck"),
    url(r'^edit_truck/(?P<truck_id>\d+)/$', TruckUpdateView.as_view(), name="truck_edit"),

    url(r'^employees/$', EmployeeListView.as_view(), name="employee_list"),
    url(r'^employee_create/$', EmployeeCreateView.as_view(), name="employee_create"),
    url(r'^employee_edit/(?P<employee_id>\d+)/$', EmployeeUpdateView.as_view(), name="employee_edit"),
]
