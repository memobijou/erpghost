from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import datetime

# Create your views here.
from order.models import Order
from mission.models import Mission
from product.models import Product
from stock.models import Stock
from django.db.models import Sum


@login_required
def main_view(request):
    context = {}
    context["title"] = "Wilkommen auf ERPGhost"
    today = datetime.datetime.today()
    context["products"] = Product.objects.all()
    context["whole_stocking"] = Stock.objects.all().aggregate(Sum('bestand'))
    context["orders"] = Order.objects.filter(delivery_date__lte=today).order_by('-delivery_date')[:5]
    context["missions"] = Mission.objects.filter(delivery_date__lte=today).order_by('-delivery_date')[:5]
    return render(request, "main/main.html", context)
