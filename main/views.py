from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import datetime

# Create your views here.
from order.models import Order
from mission.models import Mission
from product.models import Product
from stock.models import Stock
from django.db.models import Sum
from django.db.models import F, Func


@login_required
def main_view(request):
    context = {}
    context["title"] = "Wilkommen auf ERPGhost"
    today = datetime.datetime.today()
    context["products"] = Product.objects.all()
    context["whole_stocking"] = Stock.objects.all().aggregate(Sum('bestand'))

    orders = Order.objects.all().annotate(
        delta=Func((F('delivery_date') - datetime.date.today()), function='ABS')).order_by("delta").distinct()[:10]

    missions = Mission.objects.all().annotate(
        delta=Func((F('delivery_date') - datetime.date.today()), function='ABS')).order_by("delta").distinct()[:10]

    context["orders"] = orders
    context["missions"] = missions
    return render(request, "main/main.html", context)
