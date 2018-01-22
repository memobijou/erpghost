from django.shortcuts import render


# Create your views here.

def main_view(request):
    context = {}
    context["title"] = "Wilkommen auf ERPGhost"

    return render(request, "main/main.html", context)
