from django.shortcuts import render
from django.views import View

from mission.models import Mission


class CalendarView(View):
    def get(self, request):
        return render(request, "disposition/calendar.html", self.build_context())

    def build_context(self):
        context = {"title": "Disposition",
                   "missions": Mission.objects.all()}
        return context