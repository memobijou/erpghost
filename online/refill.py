from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View

from configuration.models import OnlinePositionPrefix
from mission.models import Mission, ProductMission
from online.models import RefillOrder, RefillOrderOutbookStock
from online.pick import order_stocks_by_position
from product.models import Product
from stock.models import Stock


class AcceptRefillStockView(View):
    template_name = "online/refill/accept_refill.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.missions = Mission.objects.filter(channel__isnull=False, is_amazon_fba=False,
                                               productmission__product__ean__isnull=False,
                                               online_picklist__isnull=True)
        self.missions_products = self.get_missions_products()
        self.missions_products_stocks = self.get_missions_products_stocks()
        self.missions_products_and_stocks = self.get_missions_products_and_stocks()
        self.products = None
        self.refillorder = None

    def dispatch(self, request, *args, **kwargs):
        self.refillorder = request.user.refillorder_set.filter(completed=None).first()
        if self.refillorder is not None:
            return HttpResponseRedirect(reverse_lazy("online:refill"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def post(self, request, *args, **kwargs):
        self.create_refill_order()
        return HttpResponseRedirect(reverse_lazy("online:refill"))

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
                        (stock.product is not None and stock.product.ean == mission_product.product.ean)):
                    if sum_bookout_amount == mission_product.amount:
                        break

                    bookout_amount = 0

                    if sum_bookout_amount + stock.bestand <= mission_product.amount:
                        bookout_amount = stock.bestand
                        sum_bookout_amount += bookout_amount
                    elif sum_bookout_amount + stock.bestand > mission_product.amount:
                        bookout_amount = mission_product.amount - sum_bookout_amount
                        sum_bookout_amount += bookout_amount

                    mission_product_stocks.append({"object": stock, "bookout_amount": bookout_amount})
        return self.missions_products_and_stocks

    def get_missions_products(self):
        mission_pks = [mission.pk for mission in self.missions]
        missions_products = ProductMission.objects.filter(mission__in=mission_pks)
        return missions_products

    def get_missions_products_stocks(self):
        ean_list = []

        for mission_product in self.missions_products:
            ean_list.append(mission_product.product.ean)
        print(ean_list)
        online_prefixes = OnlinePositionPrefix.objects.all()
        exclude_condition = Q()
        for online_prefix in online_prefixes:
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
        self.refillorder = RefillOrder.objects.filter(user=self.request.user).first()
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

    def dispatch(self, request, *args, **kwargs):
        self.object = Stock.objects.get(pk=self.kwargs.get("pk"))
        self.book_out_amount = self.kwargs.get("book_out_amount")
        self.product = self.get_product()
        return super().dispatch(request, *args, **kwargs)

    def get_product(self):
        if self.object.product is not None:
            self.product = self.object.product
        else:
            if self.object.ean_vollstaendig is not None:
                self.product = Product.objects.filter(ean=self.object.ean_vollstaendig).first()
            else:
                self.product = Product.objects.filter(sku__sku=self.object.sku).first()
        return self.product

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def post(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse_lazy('online:'))

    def get_context(self):
        context = {"title": "Bestand ausbuchen", "object": self.object, "book_out_amount": self.book_out_amount,
                   "product": self.product}
        return context