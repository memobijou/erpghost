from django.conf.urls import url

from disposition.views import CalendarView, TruckUpdateView, TruckListView, TruckCreateView, EmployeeListView, \
    EmployeeCreateView, EmployeeUpdateView

urlpatterns = [
    url(r'^$', CalendarView.as_view(), name="calendar"),
    url(r'^edit/(?P<truck_id>\d+)/$', TruckUpdateView.as_view(), name="truck_edit"),
    url(r'^trucks/$', TruckListView.as_view(), name="truck_list"),
    url(r'^create/(?P<delivery_note_number>\w+)/$', TruckCreateView.as_view(), name="truck_create"),
    url(r'^employees/$', EmployeeListView.as_view(), name="employee_list"),
    url(r'^employee_create/$', EmployeeCreateView.as_view(), name="employee_create"),
    url(r'^employee_edit/(?P<employee_id>\d+)/$', EmployeeUpdateView.as_view(), name="employee_edit"),
]
