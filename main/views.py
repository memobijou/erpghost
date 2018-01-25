from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def main_view(request):
    context = {}
    context["title"] = "Wilkommen auf ERPGhost"

    return render(request, "main/main.html", context)
