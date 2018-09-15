from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View

from configuration.models import OnlinePositionPrefix
from online.forms import BookinForm
from mission.models import Mission, ProductMission
from online.models import RefillOrder, RefillOrderOutbookStock, RefillOrderInbookStock
from online.pick import order_stocks_by_position
from product.models import Product
from stock.models import Stock
from django.views import generic
from stock.models import Position
from mission.models import PackingStation


class AcceptRefillStockView(View):
    template_name = "online/refill/accept_refill.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.online_prefixes = OnlinePositionPrefix.objects.all()
        self.missions = Mission.objects.filter(channel__isnull=False, is_amazon_fba=False,
                                               productmission__product__ean__isnull=False,
                                               online_picklist__isnull=True)
        self.missions_products = self.get_missions_products()
        self.remove_missions_products_with_online_stock()
        self.missions_products_stocks = self.get_missions_products_stocks()
        self.missions_products_and_stocks = self.get_missions_products_and_stocks()
        self.refillorder = None
        self.existing_refillorder_stocks = None

    def dispatch(self, request, *args, **kwargs):
        self.refillorder = request.user.refillorder_set.filter(Q(Q(booked_out=None) | Q(booked_in=None))).first()

        if self.refillorder is not None:
            return HttpResponseRedirect(reverse_lazy("online:refill"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def post(self, request, *args, **kwargs):
        self.create_refill_order()
        return HttpResponseRedirect(reverse_lazy("online:refill"))

    def remove_missions_products_with_online_stock(self):
        products = [mission_product.product for mission_product in self.missions_products]
        ean_list = [mission_product.product.ean for mission_product in self.missions_products]

        for mission_product in self.missions_products:
            products.append(mission_product.product)

        query_condition = Q()
        for online_prefix in self.online_prefixes:
            query_condition |= Q(lagerplatz__istartswith=online_prefix.prefix)
        query_condition &= Q(Q(product__in=products) | Q(ean_vollstaendig__in=ean_list))
        query_condition &= Q(zustand__iexact="Neu")
        online_stocks = Stock.objects.filter(query_condition)
        products_online_stocks = {}
        for mission_product in self.missions_products:
            product = mission_product.product
            products_online_stocks[product] = 0
            for online_stock in online_stocks:
                if ((online_stock.product == product or online_stock.ean_vollstaendig == product.ean) and
                        (online_stock.zustand == "Neu")):
                    products_online_stocks[product] += online_stock.bestand
        print(products_online_stocks)
        exclude_missions_products_pks = []
        for mission_product in self.missions_products:
            if products_online_stocks.get(mission_product.product) >= mission_product.amount:
                exclude_missions_products_pks.append(mission_product.pk)
        self.missions_products = self.missions_products.exclude(pk__in=exclude_missions_products_pks)

    def create_refill_order(self):
        self.refillorder = RefillOrder.objects.create(user=self.request.user)
        bulk_instances = []
        for mission_product, stocks in self.missions_products_and_stocks:
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
                   "missions_products_and_stocks": self.missions_products_and_stocks}
        if self.missions.count() == 0:
            context["title"] = "Keine Online Aufträge vorhanden"
        return context

    def get_missions_products_and_stocks(self):
        self.missions_products_and_stocks = []

        for mission_product in self.missions_products:
            mission_product_stocks = []
            mission_product_and_stocks = (mission_product, mission_product_stocks)
            self.missions_products_and_stocks.append(mission_product_and_stocks)

            sum_bookout_amount = 0

            for stock in self.missions_products_stocks:
                if (stock.ean_vollstaendig == mission_product.product.ean or
                        (stock.product is not None and stock.product.ean == mission_product.product.ean)
                        and stock.zustand == "Neu"):
                    if sum_bookout_amount == mission_product.amount:
                        break

                    bookout_amount = 0

                    if sum_bookout_amount + stock.bestand <= mission_product.amount:
                        bookout_amount = stock.bestand
                        sum_bookout_amount += bookout_amount
                    elif sum_bookout_amount + stock.bestand > mission_product.amount:
                        bookout_amount = mission_product.amount - sum_bookout_amount
                        sum_bookout_amount += bookout_amount
                    print(f"wieeee: {sum_bookout_amount}")
                    mission_product_stocks.append({"object": stock, "bookout_amount": bookout_amount})
        return self.missions_products_and_stocks

    def get_missions_products(self):
        mission_pks = [mission.pk for mission in self.missions]
        missions_products = ProductMission.objects.filter(mission__in=mission_pks)

        exclude_pks = []
        for mission_product in missions_products:
            refillorder_stock_instance = RefillOrderOutbookStock.objects.filter(product_mission=mission_product).first()

            stock = mission_product.product.stock_set.filter(zustand="Neu").first()
            if stock is None:
                product = mission_product.product
                products_sku = product.sku_set.filter(state__iexact="Neu")
                stock = Stock.objects.filter(Q(Q(ean_vollstaendig=product.ean,
                                             zustand__iexact="Neu") |
                                               Q(product__ean=product.ean, sku=products_sku.sku))
                                             ).first()
            available_amount = int(stock.get_total_stocks().get("Neu").split("/")[0])
            if available_amount < mission_product.amount or refillorder_stock_instance is not None:
                exclude_pks.append(mission_product.pk)
        return missions_products.exclude(pk__in=exclude_pks)

    def get_missions_products_stocks(self):
        ean_list = []

        for mission_product in self.missions_products:
            ean_list.append(mission_product.product.ean)
        print(ean_list)
        self.online_prefixes = OnlinePositionPrefix.objects.all()
        exclude_condition = Q()
        for online_prefix in self.online_prefixes:
            exclude_condition |= Q(lagerplatz__istartswith=online_prefix.prefix)
        query_condition = Q(product__ean__in=ean_list)
        stocks = list(Stock.objects.filter(query_condition).exclude(exclude_condition).order_by("lagerplatz"))
        print(stocks)
        stocks = order_stocks_by_position(stocks, query_condition=query_condition, exclude_condition=exclude_condition)
        print(f"samu: {stocks}")
        return stocks


class RefillStockView(View):
    template_name = "online/refill/refill.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.refillorder = None

    def dispatch(self, request, *args, **kwargs):
        self.refillorder = RefillOrder.objects.filter(Q(Q(booked_out=None) | Q(booked_in=None)) &
                                                      Q(user=self.request.user)).first()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def get_context(self):
        context = {"title": "Nachfüllauftrag", "refillorder": self.refillorder}
        return context


class BookOutForOnlinePositions(View):
    template_name = "online/refill/bookout.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None
        self.book_out_amount = None
        self.product = None
        self.refill_order = None

    def dispatch(self, request, *args, **kwargs):
        self.object = RefillOrderOutbookStock.objects.get(pk=self.kwargs.get("pk"))
        self.book_out_amount = self.kwargs.get("book_out_amount")
        self.product = self.get_product()
        self.refill_order = self.object.refill_order
        return super().dispatch(request, *args, **kwargs)

    def get_product(self):
        if self.object.product_mission.product is not None:
            self.product = self.object.product_mission.product
        else:
            if self.object.ean_vollstaendig is not None:
                self.product = Product.objects.filter(ean=self.object.ean_vollstaendig).first()
            else:
                self.product = Product.objects.filter(sku__sku=self.object.sku).first()
        return self.product

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def post(self, request, *args, **kwargs):
        self.bookout_stock()
        return HttpResponseRedirect(reverse_lazy('online:refill'))

    def bookout_stock(self):
        stock, bookout_amount = self.object.stock, self.object.amount
        available_amount = int(self.object.stock.get_total_stocks().get("Neu").split("/")[0])
        max_bookout_amount = 0
        print(f"test: {stock.lagerplatz} - {stock.bestand} - {available_amount} - {bookout_amount}")
        if stock.bestand <= available_amount:
            max_bookout_amount = stock.bestand
        elif stock.bestand > available_amount:
            max_bookout_amount = available_amount

        if bookout_amount <= max_bookout_amount and self.object.booked_out is not True:
            print(f"OK GO {bookout_amount}")
            self.object.booked_out = True
            self.object.save()
            if stock.bestand - bookout_amount <= 0:
                stock.delete()
            else:
                stock.bestand -= bookout_amount
                stock.save()
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
            if product not in products:
                inbook_stocks = self.refill_order.refillorderinbookstock_set.filter(product=product)
                products.append((product, inbook_stocks))
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
        self.product, self.position, self.form, self.refill_order = None, None, None, None
        self.bookin_amount, self.booked_in_amount, self.booked_out_amount = 0, 0, 0
        self.stock = None

    def dispatch(self, request, *args, **kwargs):
        self.product = Product.objects.get(pk=self.kwargs.get("product_pk"))
        self.position = Position.objects.get(pk=self.kwargs.get("position_pk"))
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
                   "form": self.form, "refill_order": self.refill_order}
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
        query_condition = Q(Q(product=self.product, lagerplatz__iexact=self.position.name, zustand="Neu")
                            | (Q(ean_vollstaendig=self.product.ean, lagerplatz__iexact=self.position.name,
                                 zustand="Neu")))
        self.stock = Stock.objects.filter(query_condition).first()
        print(f"bbaba: {self.position.name} - {self.stock}")
        if self.stock is None:
            self.stock = Stock(ean_vollstaendig=self.product.ean, zustand="Neu", lagerplatz=self.position.name,
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
                                              booked_in=True, stock=self.stock)

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
            if product not in self.refill_order_result:
                self.refill_order_result[product] = {}

            if "booked_out" not in self.refill_order_result[product]:
                self.refill_order_result[product]["booked_out"] = bookout_amount
            else:
                self.refill_order_result[product]["booked_out"] += bookout_amount

        for inbook_product in self.refill_order.refillorderinbookstock_set.all():
            bookin_amount = inbook_product.amount
            product = inbook_product.product

            if product not in self.refill_order_result:
                self.refill_order_result[product] = {}

            if "booked_in" not in self.refill_order_result[product]:
                self.refill_order_result[product]["booked_in"] = bookin_amount
            else:
                self.refill_order_result[product]["booked_in"] += bookin_amount
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
        self.station = PackingStation.objects.filter(pickorder__isnull=False, user__isnull=True).first()

        if self.station is not None:
            return HttpResponseRedirect(reverse_lazy("online:login_station"))

        self.pick_order = request.user.pickorder_set.filter(completed=None).first()

        if self.pick_order is not None:
            return HttpResponseRedirect(reverse_lazy("online:picking"))
        return HttpResponseRedirect(reverse_lazy("online:accept_picklist"))
