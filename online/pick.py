import pycountry
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import generic
from django.urls import reverse_lazy
from mission.models import Mission, PickList, PickListProducts, PickOrder, PackingStation, DeliveryNote, \
    DeliveryNoteProductMission
from online.dpd import DPDLabelCreator
from online.forms import AcceptOnlinePicklistForm, PickListProductsForm, StationGotoPickListForm, PackingForm
from stock.models import Stock, Position
from configuration.models import OnlinePositionPrefix
from collections import OrderedDict
from django.db.models import Case, When
from configuration.views import PackingStationUpdate
from django.views import View
from django.contrib import messages
import re
import pycountry
from online.dhl import DHLLabelCreator
from client.models import Client


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
        self.stocks = None
        self.used_stocks = {}
        self.missions_pick_rows = None

    def dispatch(self, request, *args, **kwargs):
        self.stocks = self.get_products_stocks()
        self.picklist_data = self.get_picklist_data()
        self.missions_pick_rows = self.put_pickrows_under_missions()
        print(f"KHUTI {self.missions_pick_rows}")
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
        for mission, pick_rows in self.missions_pick_rows.items():
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
        for mission in self.missions:
            for mission_product in mission.productmission_set.all():
                picklist_stocks = []
                total = 0
                for stock in self.stocks:
                    if mission_product.product.ean == stock.product.ean:
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
                                pick_row["amount"] = difference
                                picklist_stocks.append(pick_row)

                            if stock not in self.used_stocks:
                                self.used_stocks[stock] = difference
                            else:
                                self.used_stocks[stock] += difference
                            break
                if len(picklist_stocks) > 0:
                    if mission_product.product not in picklist_data:
                        picklist_data[mission_product.product] = picklist_stocks
                    else:
                        picklist_data[mission_product.product].extend(picklist_stocks)
        print(picklist_data)
        return picklist_data

    def put_pickrows_under_missions(self):
        mission_pickrows = {}
        for product, pick_rows in self.picklist_data.items():
            for pick_row in pick_rows:
                if pick_row.get("mission_product").mission not in mission_pickrows:
                    mission_pickrows[pick_row.get("mission_product").mission] = [pick_row]
                else:
                    mission_pickrows[pick_row.get("mission_product").mission].append(pick_row)
        return mission_pickrows

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
            completed=None).order_by("mission__purchased_date").first()
        print(f"fdsafadsfds: {self.picklist}")


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
        self.mission = None
        self.client = None

    def dispatch(self, request, *args, **kwargs):
        self.picklist = PickList.objects.get(pk=self.kwargs.get("pk"))
        self.mission = self.picklist.mission_set.first()
        self.client = Client.objects.get(pk=self.request.session.get("client"))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        dhl_label = self.create_label()
        if dhl_label is not None:
            print("????!?!??!!?!?")
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

    def create_label(self):
        self.break_down_address_in_street_and_house_number()
        national_business_account = self.client.businessaccount_set.filter(type="national").first()
        foreign_country_business_account = self.client.businessaccount_set.filter(type="foreign_country").first()

        country = pycountry.countries.get(alpha_2=self.mission.delivery_address.country_code)
        if self.mission.delivery_address.strasse is not None and self.mission.delivery_address.hausnummer is not None:
            if country.name == "Germany":
                if national_business_account.transport_service.name.lower() == "dhl":
                    dhl_label = self.create_dhl_label()
                    return dhl_label
                elif national_business_account.transport_service.name.lower() == "dpd":
                    dpd_label = self.create_dpd_label()
                    return dpd_label
            else:
                if foreign_country_business_account.transport_service.name.lower() == "dhl":
                    dhl_label = self.create_dhl_label()
                    return dhl_label
                elif foreign_country_business_account.transport_service.name.lower() == "dpd":
                    dpd_label = self.create_dpd_label()
                    return dpd_label

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

    # Adresse in Stasse und Hausnummer zerlegen durch Reguläre Ausdrücke
    def break_down_address_in_street_and_house_number(self):
        mission = self.picklist.mission_set.first()
        delivery_address = mission.delivery_address
        street_and_housenumber = delivery_address.street_and_housenumber
        country_code = delivery_address.country_code
        country = pycountry.countries.get(alpha_2=country_code)

        print(f"sahbi {street_and_housenumber}")

        if country != "French" and country != "Luxenburg":
            components = re.findall(r'(\D.+)\s+(\d+.*)$', street_and_housenumber)
            components = components[0]
            print(components)
            if len(components) == 2:
                delivery_address.strasse = components[0]
                delivery_address.hausnummer = components[1]
        else:
            components = re.findall(r'^(\d+\w*)[,\s]*(\D.+)$', street_and_housenumber)
            print(components)
            if len(components) == 2:
                delivery_address.hausnummer = components[0]
                delivery_address.strasse = components[1]
        delivery_address.save()
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
