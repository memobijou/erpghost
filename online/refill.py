from django.db.models import OuterRef
from django.db.models import Q, Sum
from django.db.models import Subquery
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View

from configuration.models import OnlinePositionPrefix
from online.forms import BookinForm
from mission.models import Mission, ProductMission, PickOrder
from online.models import RefillOrder, RefillOrderOutbookStock, RefillOrderInbookStock
from online.pick import order_stocks_by_position
from product.models import Product
from sku.models import Sku
from stock.models import Stock
from django.views import generic
from stock.models import Position
from mission.models import PackingStation
from django.db.models import Case, When


class AcceptRefillStockView(View):
    template_name = "online/refill/accept_refill.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.online_prefixes = OnlinePositionPrefix.objects.all()
        self.missions = Mission.objects.filter(channel__isnull=False, is_amazon_fba=False,
                                               productmission__product__ean__isnull=False,
                                               online_picklist__isnull=True, is_online=True)
        self.missions_products = self.get_missions_products()
        self.missions_products_stocks = self.get_missions_products_stocks()
        self.refill_data = self.get_refill_data()
        self.refillorder = None
        self.existing_refillorder_stocks = None
        self.context = None
        self.pickorder = None
        self.online_prefixes = OnlinePositionPrefix.objects.all()

    def dispatch(self, request, *args, **kwargs):
        self.refillorder = request.user.refillorder_set.filter(Q(Q(booked_out=None) | Q(booked_in=None))).first()
        self.context = self.get_context()

        if self.refillorder is not None:
            return HttpResponseRedirect(reverse_lazy("online:refill"))
        self.pickorder = request.user.pickorder_set.filter(completed=None).first()

        if self.pickorder is not None:
            return HttpResponseRedirect(reverse_lazy("online:pickorder"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        self.create_refill_order()
        return HttpResponseRedirect(reverse_lazy("online:refill"))

    def create_refill_order(self):
        self.refillorder = RefillOrder.objects.create(user=self.request.user)
        bulk_instances = []
        for mission_product, stocks in self.refill_data:
            for stock in stocks:
                bulk_instances.append(
                    RefillOrderOutbookStock(product_mission=mission_product, amount=stock.get("bookout_amount"),
                                            position=stock.get("object").lagerplatz, refill_order=self.refillorder,
                                            stock=stock.get("object"))
                )
        RefillOrderOutbookStock.objects.bulk_create(bulk_instances)

    def get_context(self):
        context = {"missions": self.missions, "title": "Nachfüllauftrag annehmen",
                   "missions_products": self.missions_products,
                   "refill_data": self.refill_data}
        if self.missions.count() == 0:
            context["title"] = "Keine Online Aufträge vorhanden"
        return context

    def get_refill_data(self):
        added_to_refill_data_count = 0
        refill_data = []
        refill_totals = {}
        current_stock_totals = {}
        used_stocks = {}
        for mission_product in self.missions_products:
            if added_to_refill_data_count == 10:
                break

            print(f"WHAT: {mission_product.product.ean} - {mission_product.amount}")
            product, product_sku, stocks = mission_product.product, mission_product.sku, []
            total_stock = mission_product.total
            mission_product_stocks = (mission_product, stocks)

            current_mission_product_amount = 0
            refill_total = mission_product.refill_total

            if product_sku not in refill_totals:
                refill_totals[product_sku] = 0

            if product_sku not in current_stock_totals:
                current_stock_totals[product_sku] = 0

            for stock in self.missions_products_stocks:
                if stock not in used_stocks:
                    used_stocks[stock] = 0

                if (stock.ean_vollstaendig == product.ean and stock.zustand == mission_product.state) or (
                            stock.sku == product_sku):

                    if current_mission_product_amount == mission_product.amount:
                        continue

                    bookout_amount = 0

                    stock_bestand = stock.bestand - used_stocks[stock]

                    if current_mission_product_amount + stock_bestand <= mission_product.amount:
                        bookout_amount = stock_bestand

                    elif current_mission_product_amount + stock_bestand > mission_product.amount:
                        bookout_amount = mission_product.amount - current_mission_product_amount

                    if bookout_amount > 0:
                        # Falls schon Onlinebestand existiert
                        if refill_totals[product_sku] + bookout_amount > refill_total:
                            continue
                        # Falls keine Bestand mehr im Lager vorhanden
                        if current_stock_totals[product_sku] + mission_product.amount > total_stock:
                            continue

                        refill_totals[product_sku] += bookout_amount
                        current_stock_totals[product_sku] += bookout_amount
                        current_mission_product_amount += bookout_amount
                        used_stocks[stock] += bookout_amount
                        stocks.append({"object": stock, "bookout_amount": bookout_amount})

            if len(stocks) > 0 and current_mission_product_amount == mission_product.amount:
                refill_data.append(mission_product_stocks)
                added_to_refill_data_count += 1
        return refill_data

    def get_missions_products(self):

        missions_products = ProductMission.objects.get_online_stocks().filter(
            mission__in=self.missions.values_list("pk", flat=True)).order_by("mission__purchased_date")

        exclude_pks = []
        for mission_product in missions_products:
            refillorder_stock_instance = RefillOrderOutbookStock.objects.filter(
                product_mission=mission_product, booked_out=None).first()

            if refillorder_stock_instance is not None:
                exclude_pks.append(mission_product.pk)
        print(len(exclude_pks))
        missions_products = missions_products.exclude(pk__in=exclude_pks)
        return missions_products

    def get_missions_products_stocks(self):
        query_condition = Q()

        if self.missions_products.count() == 0:
            return

        for mission_product in self.missions_products:
            product = mission_product.product
            product_sku = mission_product.sku
            query_condition |= Q(Q(ean_vollstaendig=product.ean, zustand__iexact=mission_product.state)
                                 | Q(sku=product_sku))

        exclude_condition = Q()
        for online_prefix in self.online_prefixes:
            exclude_condition |= Q(lagerplatz__istartswith=online_prefix.prefix)
        stocks = list(Stock.objects.filter(query_condition).exclude(exclude_condition))
        print(stocks)
        stocks = order_stocks_by_position(stocks, query_condition=query_condition, exclude_condition=exclude_condition)
        return stocks


class RefillStockView(View):
    template_name = "online/refill/refill.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.refillorder = None
        self.refill_order_rows = None
        self.refill_object = None

    def dispatch(self, request, *args, **kwargs):
        self.refillorder = request.user.refillorder_set.filter(Q(Q(booked_out=None) | Q(booked_in=None))).first()
        if self.refillorder is None:
            return HttpResponseRedirect(reverse_lazy("online:accept_refill"))
        self.refill_order_rows = self.get_refill_order_rows()
        self.refill_object = self.get_refill_object()
        return super().dispatch(request, *args, **kwargs)

    def get_refill_order_rows(self):
        self.refill_order_rows = self.refillorder.refillorderoutbookstock_set.all()
        distinct_pks = self.refill_order_rows.distinct("product_mission__product", "position"
                                                       ).values_list("pk", flat=True)
        self.order_by_position(query_condition=Q(pk__in=distinct_pks))
        self.refill_order_rows = self.add_bookout_amount_to_rows()
        return self.refill_order_rows

    def get_refill_object(self):
        for refill_object, total_bookout_amount in self.refill_order_rows:
            if refill_object.booked_out is None:
                return refill_object, total_bookout_amount

    def order_by_position(self, query_condition=Q(), exclude_condition=Q()):
        stock_positions = []

        for outbook_stock in self.refill_order_rows:
            if outbook_stock.position is not None:
                position = outbook_stock.position.lower()
                if position not in stock_positions:
                    stock_positions.append(position)
            print(f"whaaaat?? : {outbook_stock.position}")
        positions = list(Position.objects.annotate(name_lower=Lower("name")).filter(
            name_lower__in=stock_positions).values_list("name", flat=True))
        print(f"ordered ? {positions}")

        positions = [position.lower() for position in positions]

        for stock_position in stock_positions:
            if stock_position.lower() not in positions:
                positions.append(stock_position)

        print(f"ordered 2? {positions}")

        positions.reverse()

        preserved = Case(*[When(position_lower=position, then=index) for index, position in enumerate(positions)])

        query_condition &= Q(position_lower__in=positions)
        self.refill_order_rows = self.refill_order_rows.annotate(position_lower=Lower("position")).filter(
            query_condition).exclude(exclude_condition).order_by(preserved)
        return self.refill_order_rows

    def add_bookout_amount_to_rows(self):
        refill_order_outbook_stocks = self.refillorder.refillorderoutbookstock_set.all()
        bookout_amounts = []
        for row in self.refill_order_rows:
            total = 0
            for outbook_stock in refill_order_outbook_stocks:
                if (outbook_stock.product_mission.product == row.product_mission.product
                        and outbook_stock.position == row.position):
                    total += outbook_stock.amount
            bookout_amounts.append(total)
        return list(zip(self.refill_order_rows, bookout_amounts))

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def get_context(self):
        context = {"title": "Nachfüllauftrag", "refillorder": self.refillorder,
                   "refill_order_rows": self.refill_order_rows, "refill_object": self.refill_object}
        return context


class BookOutForOnlinePositions(View):
    template_name = "online/refill/bookout.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None
        self.book_out_amount = None
        self.product = None
        self.refill_order = None
        self.refill_order_rows = None

    def dispatch(self, request, *args, **kwargs):
        self.object = RefillOrderOutbookStock.objects.get(pk=self.kwargs.get("pk"))
        self.product = self.get_product()
        self.refill_order = self.object.refill_order
        self.refill_order_rows = self.refill_order.refillorderoutbookstock_set.filter(
            product_mission__product=self.product, position=self.object.position)
        self.book_out_amount = self.refill_order_rows.aggregate(Sum("amount"))["amount__sum"] or 0
        return super().dispatch(request, *args, **kwargs)

    def get_product(self):
        self.product = self.object.product_mission.product
        return self.product

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def post(self, request, *args, **kwargs):
        self.bookout_stock()
        return HttpResponseRedirect(reverse_lazy('online:refill'))

    def bookout_stock(self):
        for refill_order_row in self.refill_order_rows:
            refill_order_row.refresh_from_db()
            stock, bookout_amount = refill_order_row.stock, refill_order_row.amount

            if stock is not None:
                if bookout_amount <= stock.bestand and refill_order_row.booked_out is not True:
                    if stock.bestand - bookout_amount <= 0:
                        refill_order_row.stock = None
                        refill_order_row.save()
                        stock.delete()
                    else:
                        stock.bestand -= bookout_amount
                        stock.save()
                    print(f"OK GO {bookout_amount}")
                    refill_order_row.booked_out = True
                    refill_order_row.save()
            else:
                refill_order_row.booked_out = True
                refill_order_row.save()
        self.finish_bookout()

    def finish_bookout(self):
        for bookout_row in self.refill_order.refillorderoutbookstock_set.all():
            if bookout_row.booked_out is not True:
                return
        self.refill_order.booked_out = True
        self.refill_order.save()

    def get_context(self):
        context = {"title": "Bestand ausbuchen", "object": self.object, "book_out_amount": self.book_out_amount,
                   "product": self.product, "refill_order": self.refill_order}
        return context


class BookInOnlineWarehouseList(generic.ListView):
    template_name = "online/refill/online_warehouse.html"
    paginate_by = 15

    def get_queryset(self):
        query_condition = self.build_query_condition()
        self.queryset = Position.objects.filter(query_condition)
        return self.queryset

    def build_query_condition(self):
        online_prefixes = OnlinePositionPrefix.objects.all().values_list("prefix")
        print(online_prefixes)
        query_condition = Q()
        for prefix in online_prefixes:
            query_condition |= Q(name__istartswith=prefix[0])
        print(f"banana: {self.request.GET.get('position')}")
        if self.request.GET.get('position') is not None:
            query_condition &= Q(name__icontains=self.request.GET.get('position'))
        return query_condition

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Artikel einbuchen"
        context["product"] = Product.objects.get(pk=self.kwargs.get("pk"))
        context["state"] = self.kwargs.get("state")
        return context


class ProductsForBookInView(View):
    template_name = "online/refill/products_for_bookin.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.refill_order = None
        self.products = None

    def dispatch(self, request, *args, **kwargs):
        self.refill_order = RefillOrder.objects.filter(Q(Q(booked_out=True) & Q(booked_in=None)) &
                                                       Q(user=request.user)).first()
        print(f"WWWWW {self.refill_order}")
        if self.refill_order is None:
            return HttpResponseRedirect(reverse_lazy("online:accept_refill"))
        self.products = self.get_products()
        return super().dispatch(request, *args, **kwargs)

    def get_products(self):
        products = []
        for refillorderoutbookstock in self.refill_order.refillorderoutbookstock_set.all().distinct(
                "product_mission__product"):
            product = refillorderoutbookstock.product_mission.product
            inbook_stocks = self.refill_order.refillorderinbookstock_set.filter(product=product)
            state = refillorderoutbookstock.product_mission.state
            if (product, inbook_stocks, state) not in products:
                products.append((product, inbook_stocks, state))
        return products

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def get_context(self):
        context = {"title": "Artikel in Online Lager einbuchen", "products": self.products,
                   "refill_order": self.refill_order}
        return context


class BookProductInPosition(View):
    template_name = "online/refill/book_product_in_position.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.product, self.state, self.position, self.form, self.refill_order = None, None, None, None, None
        self.bookin_amount, self.booked_in_amount, self.booked_out_amount = 0, 0, 0
        self.stock = None

    def dispatch(self, request, *args, **kwargs):
        self.product = Product.objects.get(pk=self.kwargs.get("product_pk"))
        self.position = Position.objects.get(pk=self.kwargs.get("position_pk"))
        self.state = self.kwargs.get("state")
        self.form = self.get_form()
        self.refill_order = request.user.refillorder_set.filter(Q(Q(booked_out=None) | Q(booked_in=None)) &
                                                                Q(user=self.request.user)).first()
        self.bookin_amount = self.get_bookin_amount()
        self.booked_in_amount = self.get_booked_in_amount()
        self.booked_out_amount = self.get_booked_out_amount()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def get_context(self):
        context = {"title": "Artikel in Lagerposition einbuchen", "product": self.product, "position": self.position,
                   "form": self.form, "refill_order": self.refill_order, "state": self.state}
        return context

    def get_form(self):
        if self.request.method == "POST":
            return BookinForm(data=self.request.POST)
        else:
            return BookinForm()

    def post(self, request, *args, **kwargs):
        self.validate_booked_in_amount_is_greater_than_booked_out()
        self.validate_booked_in_amount_not_exceeding_outbooked_amount()
        if self.form.is_valid() is True:
            self.bookin_product_on_position()
            self.create_refill_order_inbook_stock()
            return HttpResponseRedirect(reverse_lazy("online:products_for_bookin"))
        else:
            return render(request, self.template_name, self.get_context())

    def bookin_product_on_position(self):
        query_condition = Q(Q(product=self.product, lagerplatz__iexact=self.position.name, zustand=self.state)
                            | (Q(ean_vollstaendig=self.product.ean, lagerplatz__iexact=self.position.name,
                                 zustand=self.state)))
        self.stock = Stock.objects.filter(query_condition).first()
        print(f"bbaba: {self.position.name} - {self.stock}")
        if self.stock is None:
            self.stock = Stock(ean_vollstaendig=self.product.ean, zustand=self.state, lagerplatz=self.position.name,
                               product=self.product)
        print(f"GUTE FRAGE : {self.bookin_amount} - {self.stock.bestand}")

        print(f"bbaba2: {self.position.name} - {self.stock.lagerplatz}")

        if self.stock.bestand is not None:
            self.stock.bestand += self.bookin_amount
        else:
            self.stock.bestand = self.bookin_amount
        self.stock.save()

    def create_refill_order_inbook_stock(self):
        RefillOrderInbookStock.objects.create(refill_order=self.refill_order, product=self.product,
                                              amount=self.bookin_amount, position=self.position.name,
                                              booked_in=True, stock=self.stock, state=self.state)

    def get_bookin_amount(self):
        if self.form.is_valid() is True:
            self.bookin_amount = self.form.cleaned_data.get("bookin_amount")
        return self.bookin_amount

    def get_booked_in_amount(self):
        booked_in_sum = 0
        for inbook_stock in self.refill_order.refillorderinbookstock_set.filter(product=self.product):
            booked_in_sum += inbook_stock.amount
        return booked_in_sum

    def get_booked_out_amount(self):
        booked_out_amount = 0
        for outbook_stock in self.refill_order.refillorderoutbookstock_set.filter(
                product_mission__product=self.product):
            booked_out_amount += outbook_stock.amount
        return booked_out_amount

    def validate_booked_in_amount_not_exceeding_outbooked_amount(self):
        booked_in_sum = self.get_booked_in_amount()

        if self.booked_out_amount-(self.booked_in_amount+self.bookin_amount) < 0:
            self.form.add_error("bookin_amount", f"Sie dürfen maximal noch "
                                                 f"{self.booked_out_amount-self.booked_in_amount}x den Artikel "
                                                 f"einbuchen")

    def validate_booked_in_amount_is_greater_than_booked_out(self):
        self.booked_out_amount = self.get_booked_out_amount()
        if self.form.is_valid() is True:
            if self.bookin_amount + self.booked_in_amount > self.booked_out_amount:
                self.form.add_error("bookin_amount", f"Sie dürfen nicht mehr einbuchen als ausgebucht wurde ")
                self.form.add_error("bookin_amount", f"Sie haben den Artikel {self.booked_out_amount}x ausgebucht")


class FinishRefillOrderView(View):
    template_name = "online/refill/finish_refill_order.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context = None
        self.refill_order = None
        self.refill_order_result = {}

    def dispatch(self, request, *args, **kwargs):
        self.refill_order = request.user.refillorder_set.filter(Q(Q(booked_out=None) | Q(booked_in=None)) &
                                                                Q(user=self.request.user)).first()
        self.context = self.get_context()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        self.refill_order.booked_in = True
        self.refill_order.save()
        return HttpResponseRedirect(reverse_lazy("online:online_redirect"))

    def get_context(self):
        return {"title": "Nachfüllauftrag abschließen", "result": self.get_refill_order_result(),
                "refill_order_has_conflict": self.refill_order_has_conflict()}

    def get_refill_order_result(self):
        self.refill_order_result = {}
        for outbook_product in self.refill_order.refillorderoutbookstock_set.all():
            bookout_amount = outbook_product.amount
            product = outbook_product.product_mission.product
            state = outbook_product.product_mission.state
            if (product, state) not in self.refill_order_result:
                self.refill_order_result[(product, state)] = {}

            if "booked_out" not in self.refill_order_result[(product, state)]:
                self.refill_order_result[(product, state)]["booked_out"] = bookout_amount
            else:
                self.refill_order_result[(product, state)]["booked_out"] += bookout_amount

        for inbook_product in self.refill_order.refillorderinbookstock_set.all():
            bookin_amount = inbook_product.amount
            product = inbook_product.product
            state = inbook_product.state
            print(f"hahahahah: {inbook_product.state}")

            if (product, state) not in self.refill_order_result:
                self.refill_order_result[(product, state)] = {}

            if "booked_in" not in self.refill_order_result[(product, state)]:
                self.refill_order_result[(product, state)]["booked_in"] = bookin_amount
            else:
                self.refill_order_result[(product, state)]["booked_in"] += bookin_amount
        return self.refill_order_result

    def refill_order_has_conflict(self):
        for product, booked_data in self.refill_order_result.items():
            if booked_data.get("booked_in") != booked_data.get("booked_out"):
                return True


class OnlineRedirectView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.station = None
        self.pick_order = None

    def dispatch(self, request, *args, **kwargs):
        station_condition = Q(Q(pickorder__isnull=False, user__isnull=True) |
                              Q(pickorder__isnull=False, user=request.user))
        self.station = PackingStation.objects.filter(station_condition).first()

        if self.station is not None:
            return HttpResponseRedirect(reverse_lazy("online:login_station"))

        self.pick_order = request.user.pickorder_set.filter(completed=None).first()

        if self.pick_order is not None:
            return HttpResponseRedirect(reverse_lazy("online:picking"))
        return HttpResponseRedirect(reverse_lazy("online:accept_picklist"))
