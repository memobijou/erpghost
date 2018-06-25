from django.conf.urls import url

from disposition.views import CalendarView

urlpatterns = [
    url(r'^$', CalendarView.as_view(), name="calendar")
]