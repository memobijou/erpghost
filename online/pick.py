import pycountry
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import generic
from django.urls import reverse_lazy
from mission.models import Mission, PickList, PickListProducts, PickOrder, PackingStation, DeliveryNote, \
    DeliveryNoteProductMission
from online.forms import AcceptOnlinePicklistForm, PickListProductsForm, StationGotoPickListForm, PackingForm
from stock.models import Stock, Position
from configuration.models import OnlinePositionPrefix
from collections import OrderedDict
from django.db.models import Case, When
from configuration.views import PackingStationUpdate
from django.views import View
from django.contrib import messages


class AcceptOnlinePickList(generic.CreateView):
    template_name = "online/picklist/detail.html"
    form_class = AcceptOnlinePicklistForm
    success_url = reverse_lazy("online:pickorder")

    def __init__(self):
        super().__init__()
        self.missions = Mission.objects.filter(channel__isnull=False, is_amazon_fba=False,
                                               productmission__product__ean__isnull=False,
                                               online_picklist__isnull=True)[:10]
        self.picklist_data = None
        self.pickorder = None

    def dispatch(self, request, *args, **kwargs):
        self.picklist_data = self.get_picklist_data()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Pickauftrag annehmen"
        context["missions"] = self.missions
        context["picklist_data"] = self.picklist_data
        return context

    def form_valid(self, form):
        self.create_picklists()
        return super().form_valid(form)

    def create_picklists(self):
        self.pickorder = PickOrder.objects.create(user=self.request.user)
        for mission, pick_rows in self.picklist_data.items():
            print(f"DDD: {mission} {pick_rows}")
            picklist_instance = PickList.objects.create(pick_order=self.pickorder)
            mission.online_picklist = picklist_instance
            mission.save()
            for pick_row in pick_rows:
                pick_row_instance = PickListProducts.objects.create(
                    pick_list=picklist_instance, amount=pick_row.get("amount"), position=pick_row.get("position"),
                    product_mission=pick_row.get("mission_product")
                )
                pick_row_instance.save()
                # hier pickliste erstellen pro auftrag

    def get_picklist_data(self):
        picklist_data = OrderedDict()
        stocks = self.get_products_stocks()
        for stock in stocks:
            print(f"s {stock.lagerplatz}")
            for mission in self.missions:
                for mission_product in mission.productmission_set.all():
                    if mission_product.product.ean == stock.product.ean:
                        print(f'hehe {stock.product.ean}')
                        pick_row = {"mission_product": mission_product, "position": stock.lagerplatz}
                        if stock.bestand <= mission_product.amount:
                            pick_row["amount"] = stock.bestand
                        else:
                            pick_row["amount"] = mission_product.amount
                        if self.has_amount_of_mission_product_reached(mission_product, picklist_data) is False:
                            if mission not in picklist_data:
                                picklist_data[mission] = [pick_row]
                            else:
                                picklist_data[mission].append(pick_row)
                        stocks = self.remove_stock_from_list(stocks, stock)
        print(picklist_data)
        return picklist_data

    def has_amount_of_mission_product_reached(self, mission_product, picklist_data):
        amount = 0
        for mission, pick_rows in picklist_data.items():
            for pick_row in pick_rows:
                if pick_row.get("mission_product") == mission_product:
                    amount += pick_row.get("amount")
        if amount == mission_product.amount:
            return True
        else:
            return False

    def remove_stock_from_list(self, stocks_list, to_remove_stock):
        new_stocks_list = []
        for stock in stocks_list:
            if stock == to_remove_stock:
                pass
            else:
                new_stocks_list.append(stock)
        return new_stocks_list

    def get_products_stocks(self):
        ean_list = []
        for mission in self.missions:
            for mission_product in mission.productmission_set.all():
                ean_list.append(mission_product.product.ean)
        print(ean_list)
        online_prefixes = OnlinePositionPrefix.objects.all()
        query_condition = Q()
        for online_prefix in online_prefixes:
            query_condition &= Q(lagerplatz__istartswith=online_prefix.prefix)
        query_condition &= Q(product__ean__in=ean_list)
        stocks = list(Stock.objects.filter(query_condition).order_by("lagerplatz"))
        stocks = self.order_stocks_by_position(stocks)
        return stocks

    def order_stocks_by_position(self, stocks):
        positions = []

        for stock in stocks:
            positions.append(stock.lagerplatz)

        positions = list(Position.objects.filter(name__in=positions).values_list("name", flat=True))
        print(f"ordered ? {positions}")
        preserved = Case(*[When(lagerplatz=position, then=index) for index, position in enumerate(positions)])
        ordered_stocks = Stock.objects.filter(lagerplatz__in=positions).order_by(preserved)
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
        self.picked_rows = None
        self.packing_stations = None

    def dispatch(self, request, *args, **kwargs):
        self.pickorder = request.user.pickorder_set.filter(completed=None).first()
        self.picklists = list(self.pickorder.picklist_set.all().values_list("pk", flat=True))
        self.object = PickListProducts.objects.filter(
            Q(Q(pick_list__in=self.picklists) & Q(picked=None) | Q(picked=False))).first()
        self.picked_rows = PickListProducts.objects.filter(
            Q(Q(pick_list__in=self.picklists)))
        print(f"wie: {self.picked_rows}")
        self.order_picked_rows_by_position()
        self.packing_stations = PackingStation.objects.all()
        return super().dispatch(request, *args, **kwargs)

    def order_picked_rows_by_position(self):
        positions = []

        for picked_row in self.picked_rows:
            positions.append(picked_row.position)

        positions = list(Position.objects.filter(name__in=positions).values_list("name", flat=True))
        print(f"ordered ? {positions}")
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
        print(f"wie: {self.picked_rows}")

        context["packing_stations"] = self.packing_stations
        return context

    def get_object(self, queryset=None):
        if self.request.GET.get("pk") is not None:
            self.object = PickListProducts.objects.get(pk=self.request.GET.get("pk"))
        return self.object

    def form_valid(self, form):
        self.object = self.get_object()
        instance = form.save(commit=False)
        if self.object.picked is True:
            instance.picked = None
        else:
            instance.picked = True
        return super().form_valid(form)


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
        instance.pickorder = PickOrder.objects.get(pk=self.kwargs.get("pick_order_pk"))
        instance.save()
        instance.pickorder.completed = True
        instance.pickorder.save()
        messages.success(request, f'Pickauftrag {instance.pickorder.pick_order_id} wurde erfolgreich auf der '
                                  f'Station {instance.station_id} platziert.')
        return HttpResponseRedirect(reverse_lazy('online:pickorder'))


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
            print("poca")
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
            picklistproducts__confirmed=None).order_by("mission__purchased_date").first()


class PackingPickOrderOverview(View):
    temlate_name = "online/packing/pickorder_overview.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pickorder = None
        self.packingstation = None
        self.picked_picklists = None

    def dispatch(self, request, *args, **kwargs):
        self.packingstation = PackingStation.objects.get(user=request.user)
        self.pickorder = self.packingstation.pickorder

        if self.packingstation is None or self.pickorder is None:
            return HttpResponseRedirect(reverse_lazy("online:login_station"))

        if self.pickorder is not None:
            self.picked_picklists = self.pickorder.picklist_set.filter(completed=True)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.temlate_name, self.get_context())

    def post(self, request, *args, **kwargs):
        print("wassß?? ")
        if self.request.GET.get("finish") == "1":
            print("hehe")
            self.packingstation.pickorder = None
            self.packingstation.user = None
            self.packingstation.save()
        return HttpResponseRedirect(reverse_lazy("online:login_station"))

    def get_context(self):
        context = {"title": f"Pickauftrag {self.pickorder.pick_order_id} Übersicht", "pickorder": self.pickorder,
                   "picked_picklists": self.picked_picklists}
        return context


class LoginToStationView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.packing_stations = PackingStation.objects.all()
        self.packing_station = None

    def get(self, request, *args, **kwargs):
        context = {"title": "Mit Station verbinden", "packing_stations": self.packing_stations}
        print(request.user.packingstation_set.first())
        if request.user.packingstation_set.first() is not None:
            return HttpResponseRedirect(reverse_lazy("online:from_station_to_packing",
                                                     kwargs={"pk": request.user.packingstation_set.first().pk}))
        return render(request, "online/packing/login_station.html", context)

    def post(self, request, *args, **kwargs):
        station_pk = self.request.GET.get("station_pk")
        self.packing_station = PackingStation.objects.get(pk=station_pk)
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

    def dispatch(self, request, *args, **kwargs):
        self.picklist = PickList.objects.get(pk=self.kwargs.get("pk"))
        self.mission = self.picklist.mission_set.first()
        return super().dispatch(request, *args, **kwargs)

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
        context = {"title": f"Verpacken {self.picklist.pick_id or ''}", "picklist": self.picklist, "form": self.get_form(),
                   "is_all_scanned": self.is_all_scanned(), "mission": self.mission,
                   "label_form_link": self.get_label_form_link(),
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

    def dispatch(self, request, *args, **kwargs):
        self.picklist = PickList.objects.get(pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.picklist.completed = True
        self.create_delivery_note()
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

    def book_out_stocks(self):
        for pick_row in self.picklist.picklistproducts_set.all():
            stock = Stock.objects.get(Q(Q(lagerplatz=pick_row.position)
                                        & Q(Q(ean_vollstaendig=pick_row.product_mission.product.ean) |
                                            Q(product__ean=pick_row.product_mission.product.ean)))
                                      )
            stock.bestand -= pick_row.confirmed_amount
            print(f"{stock} - {stock.bestand}")
            if stock.bestand > 0:
                stock.save()
            else:
                stock.delete()
            print(f"SO 1: {stock}")
