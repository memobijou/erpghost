import re
from collections import OrderedDict

import pycountry
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Now
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views import generic

from client.models import Client
from configuration.models import OnlinePositionPrefix
from mission.models import Mission, PickList, PickListProducts, PickOrder, PackingStation, DeliveryNote, \
    DeliveryNoteProductMission, Billing, BillingProductMission, ProductMission, DeliveryNoteItem, BillingItem
from online.dhl import DHLLabelCreator
from online.dpd import DPDLabelCreator
from online.forms import AcceptOnlinePicklistForm, PickListProductsForm, StationGotoPickListForm, PackingForm, \
    ConfirmManualForm
from sku.models import Sku
from stock.models import Stock, Position
import requests
import json
from django.db.models import Sum, Case, When, Q, F, OuterRef, Subquery, Count, ExpressionWrapper, CharField, \
    DurationField
from django.db.models.functions import Lower
import base64


class AcceptOnlinePickList(LoginRequiredMixin, generic.CreateView):
    template_name = "online/picklist/detail.html"
    form_class = AcceptOnlinePicklistForm
    success_url = reverse_lazy("online:pickorder")

    def __init__(self):
        super().__init__()
        self.pickorder_length = None
        self.missions = Mission.objects.filter(productmission__sku__product__ean__isnull=False,
                                               online_picklist__isnull=True, is_online=True, not_matchable__isnull=True,
                                               ignore_pickorder__isnull=True)
        self.missions = self.missions.annotate(delta=Case(
            When(purchased_date__gte=Now(), then=F('purchased_date') - Now()),
            When(purchased_date__lt=Now(), then=Now() - F('purchased_date')),
            output_field=DurationField())).order_by("delta")
        self.missions = self.missions.exclude(Q(
            Q(online_transport_service__name__iexact="dhl") | Q(ignore_pickorder=True))
          | Q(delta__gte=timedelta(days=20)) | Q(not_matchable=True)
        )
        self.picklist_data = None
        self.pickorder = None
        self.missions_products = None
        self.stocks = None
        self.used_stocks = {}
        self.missions_pick_rows = None
        self.packing_stations = PackingStation.objects.filter(pickorder__isnull=True)
        self.packing_station_current_user = None
        self.refill_order = None
        self.pickorder = None
        self.limit_result = None
        self.online_prefixes = OnlinePositionPrefix.objects.all()

    def dispatch(self, request, *args, **kwargs):
        self.pickorder_length = self.get_pickorder_length()
        print(f"{self.pickorder_length}")
        self.pickorder = request.user.pickorder_set.filter(completed=None).first()
        print(f"waaaaas? {self.pickorder}")
        if self.pickorder is not None:
            return HttpResponseRedirect(reverse_lazy("online:pickorder"))

        station_condition = Q(pickorder__isnull=False, user=request.user)
        self.packing_station_current_user = PackingStation.objects.filter(station_condition).first()

        if self.packing_station_current_user is not None:
            return HttpResponseRedirect(reverse_lazy("online:login_station"))

        if self.packing_stations.count() > 0:
            self.missions_products = self.get_missions_products()
            self.stocks = self.get_products_stocks()
            self.picklist_data = self.get_picklist_data()
            print(f"jo 2: {len(self.picklist_data)}")
            self.missions_pick_rows = self.put_pickrows_under_missions()
        if (self.picklist_data is None or len(self.picklist_data) == 0) and request.method == "POST":
            return HttpResponseRedirect(reverse_lazy("online:accept_picklist"))
        self.refill_order = request.user.refillorder_set.filter(Q(Q(booked_out=None) | Q(booked_in=None))).first()
        if self.refill_order is not None:
            return HttpResponseRedirect(reverse_lazy("online:refill"))
        return super().dispatch(request, *args, **kwargs)

    def get_pickorder_length(self):
        pickorder_length = self.request.GET.get("pickorder_length")
        if pickorder_length is None or pickorder_length == "":
            return 10
        return int(pickorder_length)

    def get_missions_products(self):
        product_missions = ProductMission.objects.filter(mission__pk__in=self.missions.values_list("pk", flat=True))
        product_missions = product_missions.get_online_stocks()
        print(f"banana: ")
        product_missions = product_missions.exclude(
            Q(Q(total__lte=0) | Q(online_total__lte=0) | Q(packing_unit_amount__gt=F("online_total"))))

        missions_pks = product_missions.values_list("mission__pk").order_by(
            "mission__purchased_date")[:self.pickorder_length]
        print(f"baba: ")
        print(f"{missions_pks}")
        self.missions_products = product_missions.filter(mission__pk__in=missions_pks)
        print(f"wwww:")
        return self.missions_products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Pickauftrag annehmen"
        context["pickorder_length"] = self.pickorder_length
        context["missions"] = self.missions
        context["picklist_data"] = self.picklist_data
        context["packing_stations"] = self.packing_stations
        return context

    def form_valid(self, form):
        self.create_picklists()
        return super().form_valid(form)

    def create_picklists(self):
        self.pickorder = PickOrder.objects.create(user=self.request.user)
        for mission, pick_rows in self.missions_pick_rows.items():
            picklist_instance = PickList.objects.create(pick_order=self.pickorder)
            mission.online_picklist = picklist_instance
            mission.save()

            for pick_row in pick_rows:
                mission_product = pick_row.get("mission_product")
                amount = pick_row.get("amount")
                product = mission_product.internal_sku.product

                ean = mission_product.ean
                state = mission_product.state
                # sku_number = product.sku_set.filter(main_sku=True, state=state).first().sku
                sku_number = mission_product.internal_sku_number
                online_sku = mission_product.online_sku_number

                pick_row_instance = PickListProducts.objects.create(
                    pick_list=picklist_instance, amount=amount, position=pick_row.get("position"),
                    product_mission=mission_product, ean=ean, sku_number=sku_number, online_sku_number=online_sku,
                    state=state
                )

                pick_row_instance.save()
                # hier pickliste erstellen pro auftrag

    def get_picklist_data(self):
        picklist_data = OrderedDict()

        print(f"hello:")

        for mission_product in self.missions_products:
            picklist_total = PickListProducts.objects.filter(
                pick_list__completed__isnull=True, pick_list__mission__isnull=True,
                product_mission=mission_product).aggregate(total=Sum("amount")).get("total", 0) or 0
            print(f"wie: {picklist_total}")
            picklist_stocks = []
            total = 0
            amount = mission_product.amount * mission_product.sku.product.packing_unit
            for stock in self.stocks:
                if ((stock.sku == mission_product.internal_sku_number)
                        or (mission_product.ean == stock.ean_vollstaendig and stock.zustand == mission_product.state)
                        or (stock.sku_instance.sku == mission_product.internal_sku_number
                            if stock.sku_instance is not None else False)):
                    if stock in self.used_stocks:
                        stock_bestand = stock.bestand-self.used_stocks[stock]
                    else:
                        stock_bestand = stock.bestand

                    stock_bestand -= picklist_total or 0

                    print(f"? {stock_bestand}")

                    if stock_bestand <= 0:
                        continue

                    pick_row = {"position": stock.lagerplatz, "mission_product": mission_product, "stock": stock}

                    amount = mission_product.amount*mission_product.sku.product.packing_unit

                    if (total + stock_bestand) <= amount:
                        total += stock_bestand
                        pick_row["amount"] = stock_bestand
                        picklist_stocks.append(pick_row)
                    else:
                        difference = 0
                        if (total + stock_bestand) > amount:
                            difference = amount-total

                        if difference > 0:
                            total += difference
                            pick_row["amount"] = difference
                            picklist_stocks.append(pick_row)
                            break
            if total < amount:
                continue

            if len(picklist_stocks) > 0:
                product = mission_product.sku.product
                product = product.packing_unit_parent if product.packing_unit > 1 else product
                product_data = (product, mission_product.ean, mission_product.state, mission_product.internal_sku_number)
                if product_data not in picklist_data:
                    picklist_data[product_data] = picklist_stocks
                else:
                    picklist_data[product_data].extend(picklist_stocks)

                for pick_row in picklist_stocks:
                    pick_row_stock = pick_row.get("stock")
                    if pick_row_stock not in self.used_stocks:
                        self.used_stocks[pick_row_stock] = pick_row.get("amount")
                    else:
                        self.used_stocks[pick_row_stock] += pick_row.get("amount")
        print(f"picklist_data: {picklist_data}")
        return picklist_data

    def put_pickrows_under_missions(self):
        mission_pickrows = {}
        for product_data, pick_rows in self.picklist_data.items():
            for pick_row in pick_rows:
                mission = pick_row.get("mission_product").mission
                if mission not in mission_pickrows:
                    mission_pickrows[mission] = [pick_row]
                else:
                    mission_pickrows[mission].append(pick_row)
        return mission_pickrows

    def get_products_stocks(self):
        query_condition = Q()
        print(f"okkk: {self.missions_products.count()}")
        for mission_product in self.missions_products:
            product = mission_product.internal_sku.product
            internal_sku_number = mission_product.internal_sku_number

            query_condition |= Q(Q(ean_vollstaendig=mission_product.ean, zustand__iexact=mission_product.state) |
                                 Q(sku=internal_sku_number) | Q(sku_instance__sku=internal_sku_number))

        if len(query_condition) == 0:
            return

        # for online_prefix in self.online_prefixes:
        #     query_condition &= Q(lagerplatz__istartswith=online_prefix.prefix)

        query_condition &= ~Q(lagerplatz__istartswith="block")

        stocks = list(Stock.objects.filter(query_condition))

        print(f"babo: ")

        stocks = order_stocks_by_position(stocks, query_condition=query_condition)
        print(f"Hey stocks: ")
        return stocks


def order_stocks_by_position(stocks, query_condition=Q(), exclude_condition=Q()):
    stock_positions = []

    for stock in stocks:
        position = stock.lagerplatz
        if position is not None:
            position = position.lower()
        if position not in stock_positions:
            stock_positions.append(position)

    positions = list(Position.objects.annotate(name_lower=Lower("name")).filter(
        name_lower__in=stock_positions).values_list("name_lower", flat=True))
    print(f"ordered ? {positions}")

    for stock_position in stock_positions:
        if stock_position.lower() not in [position.lower() for position in positions]:
            positions.append(stock_position)

    print(f"ordered 2? {positions}")
    preserved = Case(*[When(lagerplatz__iexact=position, then=index) for index, position in enumerate(positions)])

    query_condition &= Q(lagerplatz_lower__in=positions)
    ordered_stocks = Stock.objects.annotate(lagerplatz_lower=Lower("lagerplatz")).filter(
        query_condition).exclude(exclude_condition).order_by(preserved)

    return ordered_stocks


class PickOrderView(LoginRequiredMixin, generic.UpdateView):
    form_class = PickListProductsForm
    template_name = "online/picklist/pickorder.html"
    success_url = reverse_lazy("online:pickorder")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pickorder = None
        self.picklists = None
        self.object = None
        self.all_picked_rows = None
        self.picked_rows = None
        self.packing_stations = None

    def dispatch(self, request, *args, **kwargs):
        self.pickorder = request.user.pickorder_set.filter(completed=None).first()
        if self.pickorder is None:
            return HttpResponseRedirect(reverse_lazy("online:accept_picklist"))
        self.picklists = list(self.pickorder.picklist_set.all().values_list("pk", flat=True))
        self.all_picked_rows = PickListProducts.objects.filter(pick_list__in=self.picklists)
        picked_rows_pks = PickListProducts.objects.filter(pick_list__in=self.picklists).distinct(
            "product_mission__sku", "position").values_list("pk", flat=True)
        self.picked_rows = PickListProducts.objects.filter(
            Q(Q(pk__in=picked_rows_pks)))
        print(f"wie: {self.picked_rows}")
        self.order_picked_rows_by_position()
        self.packing_stations = PackingStation.objects.filter(pickorder__isnull=True)
        self.object = self.picked_rows.filter(Q(Q(picked=None) | Q(picked=False))).first()
        self.add_pick_amount_to_picked_rows()
        return super().dispatch(request, *args, **kwargs)

    def get_to_pick_objects_pick_amount(self):
        total = 0
        if self.object is not None:
            for pick_row in self.all_picked_rows:
                if (pick_row.product_mission.sku == self.object.product_mission.sku
                        and pick_row.position == self.object.position):
                    total += pick_row.amount
        return total

    def add_pick_amount_to_picked_rows(self):
        pick_amounts_list = []
        for pick_row in self.picked_rows:
            total = 0
            for pr in self.all_picked_rows:
                if pick_row.product_mission.sku == pr.product_mission.sku and pick_row.position == pr.position:
                    total += pr.amount
            pick_amounts_list.append(total)

        self.picked_rows = list(zip(self.picked_rows, pick_amounts_list))

    def order_picked_rows_by_position(self):
        positions = []

        for picked_row in self.picked_rows:
            positions.append(picked_row.position)

        positions = list(Position.objects.filter(name__in=positions).values_list("name", flat=True))
        print(f"ordered ? hihi {positions}")
        preserved = Case(*[When(position=position, then=index) for index, position in enumerate(positions)])
        print(positions)
        ordered_picked_rows = self.picked_rows.filter(position__in=positions).order_by(preserved)
        self.picked_rows = ordered_picked_rows
        return self.picked_rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Pickauftrag {self.pickorder.pick_order_id}"
        context["pickorder"] = self.pickorder
        context["picked_rows"] = self.picked_rows
        context["packing_stations"] = self.packing_stations
        context["object_pick_amount"] = self.get_to_pick_objects_pick_amount()
        return context

    def get_object(self, queryset=None):
        if self.request.GET.get("pk") is not None:
            self.object = PickListProducts.objects.get(pk=self.request.GET.get("pk"))
        return self.object

    def form_valid(self, form):
        self.object = self.get_object()
        instance = form.save(commit=False)
        if self.object is not None:
            if self.object.picked is True:
                for pick_row in self.all_picked_rows:
                    if (self.object.product_mission.sku == pick_row.product_mission.sku
                            and self.object.position == pick_row.position):
                        pick_row.picked = None
                        pick_row.save()
            else:
                for pick_row in self.all_picked_rows:
                    if (self.object.product_mission.sku == pick_row.product_mission.sku
                            and self.object.position == pick_row.position):
                        print(pick_row)
                        print(pick_row.picked)
                        pick_row.picked = True
                        pick_row.save()
                        print(pick_row.picked)
        return HttpResponseRedirect(self.success_url)


class PickerView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        pickorder = request.user.pickorder_set.filter(completed=None).first()

        if pickorder is not None:
            return HttpResponseRedirect(reverse_lazy('online:picking'))
        else:
            return HttpResponseRedirect(reverse_lazy('online:accept_picklist'))


class PutPickOrderOnStationView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        instance = PackingStation.objects.get(pk=self.kwargs.get("pk"))
        if instance.pickorder is None and instance.user is None:
            instance.pickorder = PickOrder.objects.get(pk=self.kwargs.get("pick_order_pk"))
            instance.save()
            instance.pickorder.completed = True
            instance.pickorder.save()
        return HttpResponseRedirect(reverse_lazy('online:online_redirect'))


class GoFromStationToPackingView(LoginRequiredMixin, View):
    form_class = StationGotoPickListForm
    template_name = "online/packing/station.html"

    def __init__(self):
        super().__init__()
        self.station = None
        self.picklist = None

    def get_success_url(self, **kwargs):
        return reverse_lazy("online:packing", kwargs={"pk": self.picklist.pk})

    def dispatch(self, request, *args, **kwargs):
        self.station = PackingStation.objects.get(pk=self.kwargs.get("pk"))
        if self.station.user != request.user:
            return HttpResponseRedirect(reverse_lazy('online:login_station'))

        self.get_earliest_purchased_picklist()

        if self.picklist is not None:
            return HttpResponseRedirect(self.get_success_url(**kwargs))
        else:
            messages.add_message(self.request, messages.INFO,
                                 "Alle Packaufträge wurden bereits gescannt und bestätigt. "
                                 "Der Pickauftrag kann unten abgeschloßen werden.")
            return HttpResponseRedirect(reverse_lazy('online:packing_overview'))

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def get_context(self):
        context = {"station": self.station, "title": f"Station {self.station.station_id}"}
        return context

    def get_earliest_purchased_picklist(self):
        self.picklist = self.station.pickorder.picklist_set.filter(
            picklistproducts__picked=True,
            completed=None).order_by("mission__purchased_date").first()
        print(f"fdsafadsfds: {self.picklist}")


class PackingPickOrderOverview(LoginRequiredMixin, View):
    template_name = "online/packing/pickorder_overview.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pickorder = None
        self.packingstation = None
        self.picklists = None
        self.picked_picklists = None

    def dispatch(self, request, *args, **kwargs):
        self.packingstation = PackingStation.objects.filter(user=request.user).first()
        if self.packingstation is None:
            return HttpResponseRedirect(reverse_lazy("online:online_redirect"))

        self.pickorder = self.packingstation.pickorder

        if self.pickorder is None:
            return HttpResponseRedirect(reverse_lazy("online:online_redirect"))

        if self.pickorder is not None:
            missions_list = []
            picklists = self.pickorder.picklist_set.filter().order_by("mission__purchased_date")
            for picklist in picklists:
                mission = picklist.mission_set.first()
                missions_list.append(mission)
            self.picked_picklists = picklists.filter(completed=True)
            self.picklists = list(zip(picklists, missions_list))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def post(self, request, *args, **kwargs):
        if self.request.GET.get("finish") == "1":
            self.packingstation.pickorder = None
            self.packingstation.user = None
            self.packingstation.save()
        return HttpResponseRedirect(reverse_lazy("online:online_redirect"))

    def get_context(self):
        context = {"title": f"Pickauftrag {self.pickorder.pick_order_id} Übersicht", "pickorder": self.pickorder,
                   "picklists": self.picklists, "picked_picklists": self.picked_picklists,
                   "can_finish_pickorder": self.can_finish_pickorder()}
        return context

    def can_finish_pickorder(self):
        for picklist in self.pickorder.picklist_set.all():
            if picklist.completed is None or picklist.completed is False:
                return False
        return True


class LoginToStationView(LoginRequiredMixin, View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.packing_stations = PackingStation.objects.all()
        self.packing_station = None
        self.station_pk = None
        self.refillorder = None
        self.pickorder = None

    def dispatch(self, request, *args, **kwargs):
        self.packing_station = request.user.packingstation_set.filter(pickorder__isnull=False).first()
        if self.packing_station is not None:
            return HttpResponseRedirect(reverse_lazy("online:from_station_to_packing",
                                                     kwargs={"pk": self.packing_station.pk}))
        self.refillorder = request.user.refillorder_set.filter(Q(Q(booked_in=None) | Q(booked_out=None))).first()

        if self.refillorder is not None:
            return HttpResponseRedirect(reverse_lazy("online:refill"))

        self.pickorder = request.user.pickorder_set.filter(completed=None).first()

        if self.pickorder is not None:
            return HttpResponseRedirect(reverse_lazy("online:pickorder"))

        connectable_station_condition = Q(pickorder__isnull=False, user__isnull=True)
        amount_empty_stations = self.packing_stations.filter(connectable_station_condition).aggregate(
            amount=Count("pk"))["amount"]

        print(f"hey: {amount_empty_stations}")

        if amount_empty_stations is None or amount_empty_stations <= 0:
            return HttpResponseRedirect(reverse_lazy("online:online_redirect"))

        self.station_pk = self.request.GET.get("station_pk")
        if self.station_pk is not None:
            for packing_station in self.packing_stations:
                if packing_station.pk == int(self.station_pk):
                    if packing_station.user is not None:
                        return HttpResponseRedirect(reverse_lazy('online:login_station'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {"title": "Mit Station verbinden", "packing_stations": self.packing_stations}
        return render(request, "online/packing/login_station.html", context)

    def post(self, request, *args, **kwargs):
        self.packing_station = PackingStation.objects.get(pk=self.station_pk)
        current_user = request.user
        self.packing_station.user = current_user
        self.packing_station.save()
        for pick_list in self.packing_station.pickorder.picklist_set.all():
            mission = pick_list.mission_set.first()
            mission.save()
        return HttpResponseRedirect(reverse_lazy("online:login_station"))


class LogoutFromStationView(LoginRequiredMixin, View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.packing_station = None

    def post(self, request, *args, **kwargs):
        station_pk = self.kwargs.get("pk")
        self.packing_station = PackingStation.objects.get(pk=station_pk)
        self.packing_station.user = None
        self.packing_station.save()
        return HttpResponseRedirect(reverse_lazy("online:login_station"))


class PackingView(LoginRequiredMixin, View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.picklist = None
        self.mission = None
        self.shipment = None
        self.pick_rows = None
        self.packingstation = None

    def dispatch(self, request, *args, **kwargs):
        self.picklist = PickList.objects.get(pk=self.kwargs.get("pk"))
        self.packingstation = PackingStation.objects.filter(user=request.user).first()
        if self.packingstation is None:
            return HttpResponseRedirect(reverse_lazy("online:online_redirect"))

        self.mission = self.picklist.mission_set.first()
        self.shipment = self.mission.get_main_shipment()
        self.pick_rows = PackingView.add_packing_amounts_to_pick_rows(self.picklist)
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def add_packing_amounts_to_pick_rows(picklist):
        pick_rows = picklist.picklistproducts_set.all().distinct("product_mission__sku")
        packing_amounts_list = []
        confirmed_amounts_list = []
        for pick_row in pick_rows:
            total = 0
            confirmed_total = 0
            for pr in picklist.picklistproducts_set.all():
                if pr.product_mission.sku == pick_row.product_mission.sku:
                    total += pr.amount or 0
                    confirmed_total += pr.confirmed_amount or 0
            packing_amounts_list.append(total)
            confirmed_amounts_list.append(confirmed_total)
        pick_rows = list(zip(pick_rows, packing_amounts_list, confirmed_amounts_list))
        return pick_rows

    def get(self, request, *args, **kwargs):
        context = self.get_context()
        return render(request, "online/packing/packing.html", context)

    @staticmethod
    def is_all_scanned(picklist):
        for pick_row in picklist.picklistproducts_set.all():
            if pick_row.confirmed is None:
                return False
        return True

    def post(self, request, *args, **kwargs):
        form = PackingForm(data=request.POST)
        context = self.get_context()

        if form.is_valid() is True:
            ean_or_sku = form.cleaned_data.get("ean_or_sku")
            pick_row = self.picklist.picklistproducts_set.filter(
                Q(Q(confirmed=None) & Q(Q(ean=ean_or_sku) | Q(sku_number=ean_or_sku)))).first()
            if pick_row is None:
                context["form"].add_error(None, f"Artikel mit EAN/SKU {ean_or_sku} in Auftrag nicht vorhanden")
                return render(request, "online/packing/packing.html", context)
            else:
                if (pick_row.confirmed_amount or 0) >= int(pick_row.amount):
                    context["form"].add_error(None, f"Artikel mit EAN/SKU {ean_or_sku}"
                                                    f" wurde bereits vollständig bestätigt")
                    return render(request, "online/packing/packing.html", context)

                if pick_row.confirmed_amount is None:
                    pick_row.confirmed_amount = 1
                else:
                    pick_row.confirmed_amount += 1

                if pick_row.amount == pick_row.confirmed_amount:
                    pick_row.confirmed = True

                pick_row.save()
            print(pick_row)
            return HttpResponseRedirect(reverse_lazy("online:packing", kwargs={"pk": self.picklist.pk}))
        else:
            return render(request, "online/packing/packing.html", context)

    def get_context(self):
        context = {"title": f"Auftrag {self.mission.mission_number or ''}", "picklist": self.picklist,
                   "form": self.get_form(), "is_all_scanned": PackingView.is_all_scanned(self.picklist),
                   "mission": self.mission, "label_form_link": self.get_label_form_link(), "pick_rows": self.pick_rows,
                   "label_link": get_label_link(self.mission), "shipment": self.shipment,
                   "total_missions_amount": PackingView.get_missions_completed_of_amount(),
                   "delivery_note_b64": self.get_delivery_note_base64(),
                   "packing_label_b64": self.get_packing_label_base64(),
                   }
        return context

    def get_packing_label_base64(self):
        if self.shipment is not None:
            encoded_string = base64.b64encode(self.shipment.label_pdf.read())
            return encoded_string.decode()

    def get_delivery_note_base64(self):
        if self.shipment is not None:
            url = self.request.build_absolute_uri(reverse("online:delivery_note", kwargs={"pk": self.shipment.pk}))
            response = requests.get(url)
            encoded_string = base64.b64encode(response.content)
            return encoded_string.decode()

    @staticmethod
    def get_missions_completed_of_amount():
        all_missions = Mission.objects.filter(
            Q(status__iexact="offen") |Q(status__icontains="station") | Q(status__iexact="am picken"))
        completed_missions = all_missions.filter(
            Q(status__iexact='verpackt'))
        return f"{all_missions.count()-completed_missions.count()}"

    def get_form(self):
        if self.request.method == "POST":
            form = PackingForm(data=self.request.POST)
        else:
            form = PackingForm()
        return form

    def get_label_form_link(self):
        business_account = self.mission.online_business_account
        if business_account.type == "national":
            return reverse_lazy(
                "online:dpd_pdf", kwargs={"pk": self.mission.pk,
                                          "business_account_pk": business_account.pk})
        if business_account.type == "foreign_country":
            return reverse_lazy("online:dhl_pdf", kwargs={"pk": self.mission.pk,
                                                          "business_account_pk": business_account.pk})


def get_label_link(mission):
    business_account = mission.online_business_account
    if business_account.type == "national":
        return reverse_lazy("online:dpd_get_label", kwargs={"pk": mission.pk})

    if business_account.type == "foreign_country":
        return reverse_lazy("online:dhl_get_label", kwargs={"pk": mission.pk,
                                                            "shipment_number": mission.tracking_number})


def book_out_stocks(picklist):
    picklist.completed = True
    picklist.save()
    for pick_row in picklist.picklistproducts_set.all():
        state = pick_row.state
        sku_number = pick_row.sku_number
        ean = pick_row.ean

        stock = Stock.objects.filter(
            Q(Q(lagerplatz__iexact=pick_row.position) &
              Q(Q(ean_vollstaendig=ean, zustand__iexact=state)
                | Q(sku=sku_number) | Q(sku_instance__sku=sku_number)))).first()

        print(f"??? {stock}")
        if stock is not None:
            stock.bestand -= pick_row.confirmed_amount

            if stock.bestand > 0:
                stock.save(hard_save=True)
            else:
                stock.delete(hard_delete=True)


class ProvidePackingView(LoginRequiredMixin, View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.picklist = None
        self.mission = None
        self.client = None
        self.transport_service = None

    def dispatch(self, request, *args, **kwargs):
        self.picklist = PickList.objects.get(pk=self.kwargs.get("pk"))
        self.mission = self.picklist.mission_set.first()
        self.client = self.mission.channel.client
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        label_or_manual_label_redirect, error = self.create_label()
        print("kommt hier")
        if error is True:
            print(label_or_manual_label_redirect)
            return label_or_manual_label_redirect
        return HttpResponseRedirect(reverse_lazy("online:packing", kwargs={"pk": self.picklist.pk}) + "?print=1")

    def create_label(self):
        if self.mission.delivery_address.strasse is None or self.mission.delivery_address.hausnummer is None:
            return HttpResponseRedirect(self.get_label_form_link()), True

        business_account = self.mission.online_business_account

        if self.mission.delivery_address.strasse is not None and self.mission.delivery_address.hausnummer is not None:
            if business_account.type == "national":
                dpd_label, message = self.create_dpd_label()
                if dpd_label is None or message != "":
                    return HttpResponseRedirect(f'{self.get_label_form_link()}?error_msg={message}'), True
                return dpd_label, None

            if business_account.type == "foreign_country":
                dhl_label = self.create_dhl_label()
                if dhl_label is None:
                    return HttpResponseRedirect(self.get_label_form_link()), True
                return dhl_label, None

    def create_dpd_label(self):
        dpd_label_creator = DPDLabelCreator(multiple_missions=[self.mission], main_shipment=True)
        dpd_label, message = dpd_label_creator.create_label()
        if dpd_label is None or dpd_label == "":
            return None, message
        return dpd_label, message

    def create_dhl_label(self):
        dhl_label_creator = DHLLabelCreator(self.mission, self.client)
        dhl_label, errors = dhl_label_creator.create_label("20", self.mission.delivery_address.first_name_last_name,
                                                           self.mission.delivery_address.strasse,
                                                           self.mission.delivery_address.hausnummer,
                                                           self.mission.delivery_address.zip,
                                                           self.mission.delivery_address.place,
                                                           self.mission.delivery_address.country_code)
        print(f"benthaus: {errors}")
        print(f"bobo: {dhl_label}")
        if errors is None:
            return dhl_label

    # alles unten ist google maps places api, muss angepasst werden

    def get_label_form_link(self):
        business_account = self.mission.online_business_account
        if business_account.type == "national":
            return reverse_lazy(
                "online:dpd_pdf", kwargs={"pk": self.mission.pk,
                                          "business_account_pk": business_account.pk}) + "?packing=1"
        if business_account.type == "foreign_country":
            return reverse_lazy("online:dhl_pdf", kwargs={"pk": self.mission.pk,
                                                          "business_account_pk": business_account.pk})


class FinishPackingView(LoginRequiredMixin, View):
    template_name = "online/packing/finish_packing.html"

    def __init__(self):
        super().__init__()
        self.mission, self.picklist = None, None
        self.shipment = None
        self.context = None
        self.pick_rows = None

    def dispatch(self, request, *args, **kwargs):
        self.picklist = PickList.objects.filter(pk=self.kwargs.get("pk")).first()
        if self.picklist.completed is True:
            return HttpResponseRedirect(reverse_lazy("online:online_redirect"))
        self.mission = self.picklist.mission_set.first() if self.picklist is not None else None
        self.pick_rows = PackingView.add_packing_amounts_to_pick_rows(self.picklist)
        self.shipment = self.mission.get_main_shipment()
        self.context = self.get_context()
        return super().dispatch(request, *args, **kwargs)

    def get_context(self):
        return {"title": f"Verpacken abschließen {self.mission.mission_number}", "picklist": self.picklist,
                "mission": self.mission, "label_link": get_label_link(self.mission), "shipment": self.shipment,
                "delivery_note_b64": self.get_delivery_note_base64(),
                "packing_label_b64": self.get_packing_label_base64(),
                "total_missions_amount": PackingView.get_missions_completed_of_amount(), "pick_rows": self.pick_rows,
                "is_all_scanned": PackingView.is_all_scanned(self.picklist)}

    def get_packing_label_base64(self):
        encoded_string = base64.b64encode(self.shipment.label_pdf.read())
        return encoded_string.decode()

    def get_delivery_note_base64(self):
        url = self.request.build_absolute_uri(reverse("online:delivery_note", kwargs={"pk": self.shipment.pk}))
        response = requests.get(url)
        encoded_string = base64.b64encode(response.content)
        return encoded_string.decode()

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        book_out_stocks(self.picklist)
        self.mission.save()
        return HttpResponseRedirect(reverse_lazy("online:online_redirect"))


class ConfirmManualView(LoginRequiredMixin, View):
    template_name = "online/packing/confirm_manual.html"

    def __init__(self):
        self.context = {}
        self.picklist = None
        self.mission = None
        self.form = None
        super().__init__()

    def dispatch(self, request, *args, **kwargs):
        self.picklist = PickList.objects.filter(pk=self.kwargs.get("pk")).first()
        if self.picklist is not None and self.picklist.completed is True:
            return HttpResponseRedirect(reverse_lazy("online:online_redirect"))
        self.mission = self.picklist.mission_set.first() if self.picklist is not None else None
        self.context.update(self.get_context())
        return super().dispatch(request, *args, **kwargs)

    def get_context(self):
        self.form = self.get_form()
        return {"title":
                f"Auftrag {self.mission.mission_number if self.mission is not None else ''} manuell erstellen",
                "form": self.form}

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        print(f"jojojo: {request.POST}")
        if self.form.is_valid() is True:
            self.mission.status = "Manuell"
            self.mission.save()
            note = self.form.cleaned_data.get("note") or ""
            if note != "":
                self.picklist.note = note

            book_out_stocks(self.picklist)
            return HttpResponseRedirect(reverse_lazy("online:online_redirect"))

    def get_form(self):
        if self.request.method == "POST":
            return ConfirmManualForm(self.request.POST)
        else:
            return ConfirmManualForm()
