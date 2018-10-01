import re
from collections import OrderedDict

import pycountry
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views import generic

from client.models import Client
from configuration.models import OnlinePositionPrefix
from mission.models import Mission, PickList, PickListProducts, PickOrder, PackingStation, DeliveryNote, \
    DeliveryNoteProductMission, Billing, BillingProductMission, ProductMission
from online.dhl import DHLLabelCreator
from online.dpd import DPDLabelCreator
from online.forms import AcceptOnlinePicklistForm, PickListProductsForm, StationGotoPickListForm, PackingForm
from sku.models import Sku
from stock.models import Stock, Position
import requests
import json
from django.db.models import Sum, Case, When, Q, F, OuterRef, Subquery, Count, ExpressionWrapper, CharField
from django.db.models.functions import Lower


class AcceptOnlinePickList(generic.CreateView):
    template_name = "online/picklist/detail.html"
    form_class = AcceptOnlinePicklistForm
    success_url = reverse_lazy("online:pickorder")

    def __init__(self):
        super().__init__()
        self.missions = Mission.objects.filter(channel__isnull=False, is_amazon_fba=False,
                                               productmission__product__ean__isnull=False,
                                               online_picklist__isnull=True, is_online=True)

        self.picklist_data = None
        self.pickorder = None
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
        self.pickorder = request.user.pickorder_set.filter(completed=None).first()
        print(f"waaaaas? {self.pickorder}")
        if self.pickorder is not None:
            return HttpResponseRedirect(reverse_lazy("online:pickorder"))
        self.stocks = self.get_products_stocks()

        station_condition = Q(pickorder__isnull=False, user=request.user)
        self.packing_station_current_user = PackingStation.objects.filter(station_condition).first()

        if self.packing_station_current_user is not None:
            return HttpResponseRedirect(reverse_lazy("online:login_station"))

        if self.packing_stations.count() > 0:
            self.picklist_data = self.get_picklist_data()
            self.missions_pick_rows = self.put_pickrows_under_missions()
        if (self.picklist_data is None or len(self.picklist_data) == 0) and request.method == "POST":
            return HttpResponseRedirect(reverse_lazy("online:accept_picklist"))
        self.refill_order = request.user.refillorder_set.filter(Q(Q(booked_out=None) | Q(booked_in=None))).first()
        if self.refill_order is not None:
            return HttpResponseRedirect(reverse_lazy("online:refill"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Pickauftrag annehmen"
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
                print(f"DDD: {mission} - {pick_row.get('position')} - {pick_row.get('mission_product').product.ean}"
                      f" - {pick_row.get('amount')}")
                pick_row_instance = PickListProducts.objects.create(
                    pick_list=picklist_instance, amount=pick_row.get("amount"), position=pick_row.get("position"),
                    product_mission=pick_row.get("mission_product")
                )
                pick_row_instance.save()
                # hier pickliste erstellen pro auftrag

    def get_picklist_data(self):
        picklist_data = OrderedDict()
        product_missions = ProductMission.objects.filter(mission__pk__in=self.missions.values_list("pk", flat=True))

        online_prefixes_list = self.online_prefixes.annotate(prefix_lower=Lower(F("prefix"))
                                                             ).values_list("prefix_lower", flat=True)
        print(online_prefixes_list)
        online_positions_list = Position.objects.annotate(prefix_lower=Lower(F("prefix"))).filter(
            prefix_lower__in=online_prefixes_list).values_list("name", flat=True)
        print(online_positions_list.count())
        sub_sku = Sku.objects.filter(state=OuterRef("state"), product=OuterRef("product"))
        total_condition = Q(Q(product__stock__lagerplatz__in=online_positions_list)
                            & Q(Q(product__stock__sku=F("sku")) | Q(product__stock__ean_vollstaendig=F("product__ean"),
                                                                    product__stock__zustand=F("state"))))
        total_count_condition = Q(Q(product__stock__product=F("product")))
        mission_condition = Q(Q(product__productmission__product=F("product"),
                                product__productmission__state=F("state")))

        product_missions = product_missions.annotate(sku=Subquery(sub_sku.values("sku")[:1])).annotate(
            total=Sum(Case(When(total_condition, then="product__stock__bestand"), default=0))).annotate(
            mission_total=Sum(Case(When(mission_condition, then="product__productmission__amount")))).annotate(
            mission_count=Count(Case(When(mission_condition, then="product__productmission"), default=1),
                                distinct=True)).annotate(
            total_count=Count(Case(When(total_count_condition, then="product__stock"), default=1), distinct=True)
        ).annotate(
            total=F("total")/F("mission_count")).annotate(mission_total=F("mission_total")/F("total_count")).annotate(
            available_total=F("total")-F("mission_total")
        )

        exclude_missions_pks = product_missions.filter(available_total__lt=0).values_list(
            "mission__pk", flat=True)

        print(f"mama: {exclude_missions_pks}")

        product_missions = product_missions.exclude(mission__pk__in=exclude_missions_pks)

        missions_pks = product_missions.values_list("mission__pk", flat=True)[:10]
        print(f"baba: {missions_pks}")

        product_missions = product_missions.filter(mission__pk__in=missions_pks)

        for mission_product in product_missions:
            picklist_stocks = []
            total = 0

            picklist_product = PickListProducts.objects.filter(product_mission=mission_product,
                                                               amount=mission_product.amount).first()
            if picklist_product is not None:
                continue

            product = mission_product.product
            product_sku = mission_product.sku

            for stock in self.stocks:
                if ((product_sku == stock.sku) or (product.ean == stock.ean_vollstaendig
                                                   and stock.zustand == mission_product.state)):
                    if stock in self.used_stocks:
                        stock_bestand = stock.bestand-self.used_stocks[stock]
                    else:
                        stock_bestand = stock.bestand

                    if stock_bestand <= 0:
                        continue

                    pick_row = {"position": stock.lagerplatz, "mission_product": mission_product}
                    if (total + stock_bestand) <= mission_product.amount:
                        total += stock_bestand
                        pick_row["amount"] = stock_bestand
                        if stock not in self.used_stocks:
                            self.used_stocks[stock] = stock_bestand
                        else:
                            self.used_stocks[stock] += stock_bestand
                        picklist_stocks.append(pick_row)
                    else:
                        difference = 0
                        if (total + stock_bestand) > mission_product.amount:
                            difference = mission_product.amount-total

                        if difference > 0:
                            total += difference
                            pick_row["amount"] = difference
                            picklist_stocks.append(pick_row)

                        if stock not in self.used_stocks:
                            self.used_stocks[stock] = difference
                        else:
                            self.used_stocks[stock] += difference
                        break
            if total < mission_product.amount:
                continue

            if len(picklist_stocks) > 0:
                if (mission_product.product, mission_product.state, product_sku) not in picklist_data:
                    picklist_data[(mission_product.product, mission_product.state, product_sku)] = picklist_stocks
                else:
                    picklist_data[(mission_product.product, mission_product.state, product_sku)].extend(picklist_stocks)
        print(picklist_data)
        return picklist_data

    def put_pickrows_under_missions(self):
        mission_pickrows = {}
        for product, pick_rows in self.picklist_data.items():
            for pick_row in pick_rows:
                mission = pick_row.get("mission_product").mission
                if mission not in mission_pickrows:
                    mission_pickrows[mission] = [pick_row]
                else:
                    mission_pickrows[mission].append(pick_row)
        return mission_pickrows

    def get_products_stocks(self):
        query_condition = Q()

        for mission in self.missions:
            for mission_product in mission.productmission_set.all():
                product = mission_product.product
                products_sku = product.sku_set.filter(state__iexact=mission_product.state).first()

                query_condition |= Q(Q(ean_vollstaendig=product.ean, zustand__iexact=mission_product.state) |
                                     Q(sku=products_sku.sku))

        if len(query_condition) == 0:
            return

        for online_prefix in self.online_prefixes:
            query_condition &= Q(lagerplatz__istartswith=online_prefix.prefix)

        stocks = list(Stock.objects.filter(query_condition))

        stocks = order_stocks_by_position(stocks, query_condition=query_condition)
        return stocks


def order_stocks_by_position(stocks, query_condition=Q(), exclude_condition=Q()):
    positions = []

    for stock in stocks:
        positions.append(stock.lagerplatz)

    positions = list(Position.objects.filter(name__in=positions).values_list("name", flat=True))
    print(f"ordered ? {positions}")
    preserved = Case(*[When(lagerplatz=position, then=index) for index, position in enumerate(positions)])

    query_condition &= Q(lagerplatz__in=positions)
    ordered_stocks = Stock.objects.filter(query_condition).exclude(exclude_condition).order_by(preserved)
    return ordered_stocks


class PickOrderView(generic.UpdateView):
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
            "product_mission__product", "position").values_list("pk", flat=True)
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
                if (pick_row.product_mission.product == self.object.product_mission.product
                        and pick_row.position == self.object.position):
                    total += pick_row.amount
        return total

    def add_pick_amount_to_picked_rows(self):
        pick_amounts_list = []
        for pick_row in self.picked_rows:
            total = 0
            for pr in self.all_picked_rows:
                if pick_row.product_mission.product == pr.product_mission.product and pick_row.position == pr.position:
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
                    if (self.object.product_mission.product == pick_row.product_mission.product
                            and self.object.position == pick_row.position):
                        pick_row.picked = None
                        pick_row.save()
            else:
                for pick_row in self.all_picked_rows:
                    if (self.object.product_mission.product == pick_row.product_mission.product
                            and self.object.position == pick_row.position):
                        print(f"akhira: {pick_row.product_mission.product.ean}")
                        print(pick_row)
                        print(pick_row.picked)
                        pick_row.picked = True
                        pick_row.save()
                        print(pick_row.picked)
        return HttpResponseRedirect(self.success_url)


class PickerView(View):
    def get(self, request, *args, **kwargs):
        pickorder = request.user.pickorder_set.filter(completed=None).first()

        if pickorder is not None:
            return HttpResponseRedirect(reverse_lazy('online:picking'))
        else:
            return HttpResponseRedirect(reverse_lazy('online:accept_picklist'))


class PutPickOrderOnStationView(View):
    def post(self, request, *args, **kwargs):
        instance = PackingStation.objects.get(pk=self.kwargs.get("pk"))
        if instance.pickorder is None and instance.user is None:
            instance.pickorder = PickOrder.objects.get(pk=self.kwargs.get("pick_order_pk"))
            instance.save()
            instance.pickorder.completed = True
            instance.pickorder.save()
        return HttpResponseRedirect(reverse_lazy('online:online_redirect'))


class GoFromStationToPackingView(View):
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


class PackingPickOrderOverview(View):
    template_name = "online/packing/pickorder_overview.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pickorder = None
        self.packingstation = None
        self.picked_picklists = None

    def dispatch(self, request, *args, **kwargs):
        self.packingstation = PackingStation.objects.filter(user=request.user).first()
        if self.packingstation is None:
            return HttpResponseRedirect(reverse_lazy("online:login_station"))

        self.pickorder = self.packingstation.pickorder

        if self.pickorder is None:
            return HttpResponseRedirect(reverse_lazy("online:login_station"))

        if self.pickorder is not None:
            missions_list = []
            picked_picklists = self.pickorder.picklist_set.filter(completed=True)
            for picklist in picked_picklists:
                mission = picklist.mission_set.first()
                missions_list.append(mission)
            self.picked_picklists = list(zip(picked_picklists, missions_list))
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
                   "picked_picklists": self.picked_picklists, "can_finish_pickorder": self.can_finish_pickorder()}
        return context

    def can_finish_pickorder(self):
        for picklist in self.pickorder.picklist_set.all():
            if picklist.completed is None or picklist.completed is False:
                return False
        return True


class LoginToStationView(View):
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
        return HttpResponseRedirect(reverse_lazy("online:login_station"))


class LogoutFromStationView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.packing_station = None

    def post(self, request, *args, **kwargs):
        station_pk = self.kwargs.get("pk")
        self.packing_station = PackingStation.objects.get(pk=station_pk)
        self.packing_station.user = None
        self.packing_station.save()
        return HttpResponseRedirect(reverse_lazy("online:login_station"))


class PackingView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.picklist = None
        self.mission = None
        self.pick_rows = None

    def dispatch(self, request, *args, **kwargs):
        self.picklist = PickList.objects.get(pk=self.kwargs.get("pk"))
        self.mission = self.picklist.mission_set.first()
        self.pick_rows = self.picklist.picklistproducts_set.all().distinct("product_mission__product")
        self.add_packing_amounts_to_pick_rows()
        return super().dispatch(request, *args, **kwargs)

    def add_packing_amounts_to_pick_rows(self):
        packing_amounts_list = []
        confirmed_amounts_list = []
        for pick_row in self.pick_rows:
            total = 0
            confirmed_total = 0
            for pr in self.picklist.picklistproducts_set.all():
                if pr.product_mission.product == pick_row.product_mission.product:
                    total += pr.amount or 0
                    confirmed_total += pr.confirmed_amount or 0
            packing_amounts_list.append(total)
            confirmed_amounts_list.append(confirmed_total)
        self.pick_rows = list(zip(self.pick_rows, packing_amounts_list, confirmed_amounts_list))

    def get(self, request, *args, **kwargs):
        context = self.get_context()
        return render(request, "online/packing/packing.html", context)

    def is_all_scanned(self):
        print(f"haaa: {self.picklist}")
        for pick_row in self.picklist.picklistproducts_set.all():
            if pick_row.confirmed is None:
                return False
        return True

    def post(self, request, *args, **kwargs):
        form = PackingForm(data=request.POST)
        context = self.get_context()

        if form.is_valid() is True:
            ean = form.cleaned_data.get("ean")
            pick_row = self.picklist.picklistproducts_set.filter(
                product_mission__product__ean=ean, confirmed=None).first()
            if pick_row is None:
                context["form"].add_error(None, f"Artikel mit EAN {ean} in Auftrag nicht vorhanden")
                return render(request, "online/packing/packing.html", context)
            else:
                if (pick_row.confirmed_amount or 0) >= int(pick_row.amount):
                    context["form"].add_error(None, f"Artikel mit EAN {ean} wurde bereits vollständig bestätigt")
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
                   "form": self.get_form(), "is_all_scanned": self.is_all_scanned(), "mission": self.mission,
                   "label_form_link": self.get_label_form_link(), "pick_rows": self.pick_rows,
                   "is_delivery_address_national": self.is_delivery_address_national()}
        return context

    def get_form(self):
        if self.request.method == "POST":
            form = PackingForm(data=self.request.POST)
        else:
            form = PackingForm()
        return form

    def get_label_form_link(self):
        if self.mission.delivery_address is not None and self.mission.delivery_address.country_code is not None:
            delivery_address_country_code = self.mission.delivery_address.country_code
            country = pycountry.countries.get(alpha_2=delivery_address_country_code)
            transport_accounts = self.mission.channel.api_data.client.businessaccount_set.all()
            for transport_account in transport_accounts:
                print(f"{transport_account.type} : {country}")
                if transport_account.type == "national" and country.name == "Germany":
                    return reverse_lazy("online:dpd_pdf", kwargs={"pk": self.mission.pk,
                                                                  "business_account_pk": transport_account.pk})
                elif transport_account.type == "foreign_country" and country.name != "Germany":
                    return reverse_lazy("online:dhl_pdf", kwargs={"pk": self.mission.pk,
                                                                  "business_account_pk": transport_account.pk})
            return ""

    def is_delivery_address_national(self):
        if self.mission.delivery_address is not None and self.mission.delivery_address.country_code is not None:
            delivery_address_country_code = self.mission.delivery_address.country_code
            country = pycountry.countries.get(alpha_2=delivery_address_country_code)
            print(country.name)
            print(self.mission.channel.api_data.client.businessaccount_set.all())

            if country.name == "Germany":
                return True
            else:
                return False


class FinishPackingView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.picklist = None
        self.mission = None
        self.client = None

    def dispatch(self, request, *args, **kwargs):
        self.picklist = PickList.objects.get(pk=self.kwargs.get("pk"))
        self.mission = self.picklist.mission_set.first()
        self.client = Client.objects.get(pk=self.request.session.get("client"))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        label_or_manual_label_redirect, error = self.create_label()
        if error is True:
            print(label_or_manual_label_redirect)
            return label_or_manual_label_redirect
        if label_or_manual_label_redirect is not None and error is None:
            print("????!?!??!!?!?")
            self.picklist.completed = True
            self.create_delivery_note()
            self.create_billing()
            self.book_out_stocks()
        return HttpResponseRedirect(reverse_lazy("online:packing", kwargs={"pk": self.picklist.pk}))

    def create_delivery_note(self):
        self.picklist.online_delivery_note = DeliveryNote.objects.create()
        self.picklist.save()
        bulk_instances = []
        for pick_row in self.picklist.picklistproducts_set.all():
            bulk_instances.append(DeliveryNoteProductMission(product_mission=pick_row.product_mission,
                                                             delivery_note=self.picklist.online_delivery_note,
                                                             amount=pick_row.confirmed_amount, ))
        DeliveryNoteProductMission.objects.bulk_create(bulk_instances)

    def create_billing(self):
        self.picklist.online_billing = Billing.objects.create()
        self.picklist.save()
        bulk_instances = []

        for pick_row in self.picklist.picklistproducts_set.all():
            bulk_instances.append(BillingProductMission(product_mission=pick_row.product_mission,
                                                        billing=self.picklist.online_billing,
                                                        amount=pick_row.confirmed_amount, ))
        BillingProductMission.objects.bulk_create(bulk_instances)

    def create_label(self):
        error = self.break_down_address_in_street_and_house_number()
        if error is True:
            return HttpResponseRedirect(self.get_label_form_link()), True
        national_business_account = self.client.businessaccount_set.filter(type="national").first()
        foreign_country_business_account = self.client.businessaccount_set.filter(type="foreign_country").first()

        country = pycountry.countries.get(alpha_2=self.mission.delivery_address.country_code)
        if self.mission.delivery_address.strasse is not None and self.mission.delivery_address.hausnummer is not None:
            if country.name == "Germany":
                if national_business_account.transport_service.name.lower() == "dhl":
                    dhl_label = self.create_dhl_label()
                    return dhl_label, None
                elif national_business_account.transport_service.name.lower() == "dpd":
                    dpd_label = self.create_dpd_label()
                    return dpd_label, None
            else:
                if foreign_country_business_account.transport_service.name.lower() == "dhl":
                    dhl_label = self.create_dhl_label()
                    return dhl_label, None
                elif foreign_country_business_account.transport_service.name.lower() == "dpd":
                    dpd_label = self.create_dpd_label()
                    return dpd_label, None

    def create_dpd_label(self):
        dpd_label_creator = DPDLabelCreator(self.mission, self.client)
        dpd_label = dpd_label_creator.create_label()
        return dpd_label

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

    def book_out_stocks(self):
        for pick_row in self.picklist.picklistproducts_set.all():
            product = pick_row.product_mission.product
            product_sku = product.sku_set.filter(state__iexact=pick_row.product_mission.state).first()
            stock = Stock.objects.get(Q(Q(lagerplatz__iexact=pick_row.position)
                                        & Q(Q(ean_vollstaendig=product.ean,
                                              zustand__iexact=pick_row.product_mission.state) |
                                            Q(sku=product_sku.sku)))
                                      )
            stock.bestand -= pick_row.confirmed_amount
            print(f"{stock} - {stock.bestand}")
            if stock.bestand > 0:
                stock.save(hard_save=True)
            else:
                stock.delete(hard_delete=True)
            print(f"SO 1: {stock}")

    # Adresse in Stasse und Hausnummer zerlegen durch Reguläre Ausdrücke
    def break_down_address_in_street_and_house_number(self):
        mission = self.picklist.mission_set.first()
        delivery_address = mission.delivery_address
        street_and_housenumber = delivery_address.street_and_housenumber
        country_code = delivery_address.country_code
        country = pycountry.countries.get(alpha_2=country_code)
        country_name = country.name

        print(f"sahbi {street_and_housenumber}")
        print(country_name)
        if country_name != "France" and country_name != "Luxenburg":
            components = re.findall(r'(\D.+)\s+(\d+.*)$', street_and_housenumber)
            if len(components) > 0:
                components = components[0]
            print(len(components))
            print(components)
            if len(components) == 2:
                print(components)
                delivery_address.strasse = components[0]
                delivery_address.hausnummer = components[1]
        else:
            components = re.findall(r'^(\d+\w*)[,\s]*(\D.+)$', street_and_housenumber)
            print(components)
            if len(components) > 0:
                components = components[0]
            if len(components) == 2:
                delivery_address.hausnummer = components[0]
                delivery_address.strasse = components[1]
        delivery_address.save()
        if delivery_address.strasse is None and delivery_address.hausnummer is None:
            return True
        print(f"sahbi {delivery_address.strasse} {delivery_address.hausnummer}")

    # alles unten ist google maps places api, muss angepasst werden

    def get_street_and_housenumber_from_shipping_address(self, shipping_address):
        street_components = {}

        if "AddressLine1" in shipping_address and "AddressLine2" in shipping_address:
            street_components["company"] = shipping_address.get("AddressLine1")
            street_components["street_and_housenumber"] = shipping_address.get("AddressLine2")
        elif "AddressLine1" in shipping_address and "AddressLine2" not in shipping_address:
            street_components["street_and_housenumber"] = shipping_address.get("AddressLine1")
        elif "AddressLine2" in shipping_address and "AddressLine1" not in shipping_address:
            street_components["street_and_housenumber"] = shipping_address.get("AddressLine2")

        return street_components

    def get_address_components_from_google_api(self, shipping_address):
        street_components = self.get_street_and_housenumber_from_shipping_address(shipping_address)

        city = shipping_address.get("City")
        postal_code = shipping_address.get("PostalCode")

        place_id = self.get_place_id_from_google_maps(street_components["street_and_housenumber"], city, postal_code)

        if place_id is None:
            return

        place_details = self.get_place_details_from_google_maps(place_id)

        if place_details is not None:
            return place_details

        # Checken ob Addresslinie 1 und 2 vorhanden, wenn ja dann, Company -> Adresse
        # Checken ob nur Addressline 1, wenn ja dann, Adresse
        # Checken ob nur Addressline 2, wenn ja dann, Adresse

        return

    def get_place_id_from_google_maps(self, street_and_housenumber, city, postal_code):
        google_maps_input = f"{street_and_housenumber} {city} {postal_code}"
        google_maps_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        query_string = f"?key={os.environ.get('GOOGLE_MAPS_KEY')}&inputtype=textquery&input={google_maps_input}"
        google_maps_url += query_string
        print(f"blablabla: {google_maps_url}")
        response = requests.get(google_maps_url)
        json_data = json.loads(response.text)

        if json_data["status"] == "ZERO_RESULTS":
            return

        if json_data["status"] == "OVER_QUERY_LIMIT":
            return

        print(json_data)
        candidates = json_data["candidates"]
        for candidate in candidates:
            print(f"{candidate}")
            place_id = candidate["place_id"]
            print(f"{place_id}")
            return place_id

    def get_place_details_from_google_maps(self, place_id):
        google_maps_url = "https://maps.googleapis.com/maps/api/place/details/json"
        query_string = f"?key={os.environ.get('GOOGLE_MAPS_KEY')}&placeid={place_id}"
        google_maps_url += query_string
        response = requests.get(google_maps_url)
        json_data = json.loads(response.text)

        if json_data["status"] == "ZERO_RESULTS":
            return

        if json_data["status"] == "OVER_QUERY_LIMIT":
            return

        result = json_data["result"]
        address_components = result["address_components"]
        street_number, route, city, postal_code = "", "", "", ""
        for address_component in address_components:
            if "street_number" in address_component.get("types"):
                street_number = address_component.get("long_name")
            if "route" in address_component.get("types"):
                route = address_component.get("long_name")
            if "locality" in address_component.get("types") and "political" in address_component.get("types"):
                city = address_component.get("long_name")
            if "postal_code" in address_component.get("types"):
                postal_code = address_component.get("long_name")
        print(f"FRONTEND: {route} {street_number} {postal_code} {city}")
        print(f"baduni {json_data}")
        return {"route": route, "street_number": street_number, "city": city, "postal_code": postal_code}

    def get_label_form_link(self):
        if self.mission.delivery_address is not None and self.mission.delivery_address.country_code is not None:
            delivery_address_country_code = self.mission.delivery_address.country_code
            country = pycountry.countries.get(alpha_2=delivery_address_country_code)
            transport_accounts = self.mission.channel.api_data.client.businessaccount_set.all()
            for transport_account in transport_accounts:
                print(f"{transport_account.type} : {country}")
                if transport_account.type == "national" and country.name == "Germany":
                    return reverse_lazy("online:dpd_pdf", kwargs={"pk": self.mission.pk,
                                                                  "business_account_pk": transport_account.pk})
                elif transport_account.type == "foreign_country" and country.name != "Germany":
                    return reverse_lazy("online:dhl_pdf", kwargs={"pk": self.mission.pk,
                                                                  "business_account_pk": transport_account.pk})
            return ""
