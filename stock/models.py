from django.db import models
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models import Sum
from django.template import Context, Template
import re

from mission.models import PartialMissionProduct, DeliveryNoteProductMission, PickListProducts, ProductMission
from product.models import Product
from sku.models import Sku


class StockQuerySet(models.QuerySet):
    def values_as_instances(self, *fields, **expressions):
        clone = self._clone()
        if expressions:
            clone = clone.annotate(**expressions)
        clone._fields = fields
        return clone

    def delete(self):
        for obj in self:
            if is_stock_reserved > 0:
                pass
            else:
                obj.delete()

    def get_stocks(self):
        from django.db.models import OuterRef, Sum, Subquery, Case, When, F
        from django.db.models.functions import Coalesce
        from mission.models import PartialMissionProduct
        states = Sku.objects.values_list("state", flat=True).distinct("state")

        total_condition = Q(Q(sku=OuterRef("sku"))
                            | Q(product__ean=OuterRef("ean_vollstaendig"), state=OuterRef("zustand")))

        get_sku_query = Sku.objects.filter(total_condition)[:1]

        total_query = Sku.objects.filter(total_condition).annotate(
            total=Coalesce(Sum("product__stock__bestand"), 0))[:1]

        online_total_condition = Q(product__productmission__product=F("product"),
                                   product__productmission__mission__is_online=True)

        online_total_query = ProductMission.objects.filter(product=OuterRef("product")).annotate(
            online_total=Sum(Case(When(online_total_condition, then="product__productmission__amount"), default=0)))[:1]

        wholesale_total_condition = Q(product_mission__product__productmission__mission__is_online__isnull=True)

        wholesale_total_query = PartialMissionProduct.objects.filter(
            product_mission__product=OuterRef("product")).annotate(
            wholesale_total=Sum(Case(When(wholesale_total_condition,
                                then="product_mission__product__productmission__partialmissionproduct__amount"),
                                     default=0
                                     )))[:1]

        queryset = self.all().annotate(state=F("sku_instance__state")).annotate(
            total=Coalesce(Subquery(total_query.values("total"), output_field=models.IntegerField()), 0)).annotate(
            online_total=Coalesce(Subquery(online_total_query.values("online_total"),
                                  output_field=models.IntegerField()), 0)).annotate(
            wholesale_total=Coalesce(Subquery(wholesale_total_query.values("wholesale_total"),
                                     output_field=models.IntegerField()), 0)).annotate(
            available_total=F("total")-F("online_total")-F("wholesale_total"))

        for state in states:

            queryset = queryset.annotate(
                **{f"sku_{state}": Subquery(Sku.objects.filter(
                    product=OuterRef("product"), state=state)[:1].values("sku"), output_field=models.CharField())})

            current_total_condition = Q(Q(sku=OuterRef(f"sku_{state}")) |
                                        Q(product__ean=OuterRef("ean_vollstaendig"), state=state))

            current_total_query = Sku.objects.filter(current_total_condition).annotate(
                total_current=Sum(Case(When(Q(Q(product__stock__zustand=state,
                                                product__stock__ean_vollstaendig=F("product__ean"))
                                              | Q(product__stock__sku=F("sku"))),
                                            then="product__stock__bestand"), default=0)))[:1]

            online_state_total_condition = Q(product__productmission__product=F("product"),
                                             product__productmission__state=state,
                                             product__productmission__mission__is_online=True)

            online_state_total_query = ProductMission.objects.filter(
                product=OuterRef("product"), state=state).annotate(
                online_state_total=Sum(Case(When(online_state_total_condition,
                                                 then="product__productmission__amount"), default=0)))[:1]

            wholesale_state_total_condition = Q(
                product_mission__product__productmission__product=F("product_mission__product"),
                product_mission__product__productmission__state=state,
                product_mission__product__productmission__mission__is_online__isnull=True)

            wholesale_total_query = PartialMissionProduct.objects.filter(
                product_mission__product=OuterRef("product"), product_mission__state=state).annotate(
                wholesale_total=Sum(Case(When(wholesale_state_total_condition,
                                              then="product_mission__product__productmission"
                                                   "__partialmissionproduct__amount"), default=0
                                         )))[:1]

            queryset = queryset.annotate(
                **{f"online_total_{state}": Coalesce(Subquery(online_state_total_query.values("online_state_total"),
                                                     output_field=models.IntegerField()), 0)})

            queryset = queryset.annotate(
                **{f"total_{state}": Coalesce(Subquery(current_total_query.values("total_current"),
                                              output_field=models.IntegerField()), 0)})

            queryset = queryset.annotate(
                **{f"wholesale_total_{state}": Coalesce(Subquery(wholesale_total_query.values("wholesale_total"),
                                                        output_field=models.IntegerField()), 0)})

            queryset = queryset.annotate(
                **{f"available_total_{state}":
                   F(f"total_{state}")-F(f"online_total_{state}")-F(f"wholesale_total_{state}")})

        return queryset

    def get_totals(self):
        from django.db.models import OuterRef, Sum, Subquery, Case, When, F
        from django.db.models.functions import Coalesce
        subquery_online_total = Sku.objects.filter(pk=OuterRef("sku_instance__pk")).annotate(
            online_total=Sum(Case(When(product__productmission__product=F("product"),
                                       product__productmission__state=F("state"),
                                       product__productmission__mission__is_online=True,
                                       then="product__productmission__amount"), default=0)))[:1]

        subquery_wholesale_total = Sku.objects.filter(pk=OuterRef("sku_instance__pk")).annotate(
            wholesale_total=Sum(Case(When(product__productmission__product=F("product"),
                                          product__productmission__state=F("state"),
                                          product__productmission__mission__is_online__isnull=True,
                                          then="product__productmission__partialmissionproduct__amount"),
                                     default=0)))[:1]
        queryset = self.all().annotate(
            total=Sum("sku_instance__stock__bestand")).annotate(
            online_total=Subquery(subquery_online_total.values("online_total"))).annotate(
            wholesale_total=Subquery(subquery_wholesale_total.values("wholesale_total"))).annotate(
            available_total=F("total")-F("online_total")-F("wholesale_total")
        )
        return queryset


class CustomManger(models.Manager):
    def get_queryset(self):
        return StockQuerySet(self.model, using=self._db)  # Important!


class StockObjectManager(CustomManger):
    def table_list(self):
        return self.all()


def is_stock_reserved(stock):
    total = PickListProducts.objects.get_stock_reserved_total(stock)
    if total is not None:
        total_reserved = total.get("total", 0) or 0
    else:
        total_reserved = 0
    print(f"{total_reserved}")
    return total_reserved


def get_states_totals_and_total_from_ean_without_product(current_stock):
    stocks = Stock.objects.filter(ean_vollstaendig=current_stock.ean_vollstaendig,
                                  zustand__in=current_stock.states).values("ean_vollstaendig", "zustand").annotate(
        total=Sum("bestand")
    )
    from collections import OrderedDict
    states_totals = OrderedDict()
    total = {"total": 0, "available_total": 0}
    for stock in stocks:
        states_totals[stock.get("zustand")] = {"total": stock.get("total"), "available_total": stock.get("total")}
        total["total"] += stock.get("total")
        total["available_total"] += stock.get("total")
    return states_totals, total


class Stock(models.Model):
    class Meta:
        ordering = ["-pk"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.states = ["Neu", "B", "C", "D", "G"]

    IGNORE_CHOICES = (
        ('IGNORE', 'Ja'),
        ('NOT_IGNORE', 'Nein'),
    )

    objects = StockObjectManager()

    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    ean_vollstaendig = models.CharField(max_length=250, verbose_name="EAN", null=True, blank=True)
    sku = models.CharField(max_length=250, verbose_name="Sku", null=True, blank=True)
    title = models.CharField(max_length=250, verbose_name="Artikelname", null=True, blank=True)
    zustand = models.CharField(max_length=250, null=True, blank=True, verbose_name="Zustand")
    ean_upc = models.CharField(max_length=250, null=True, blank=True)
    lagerplatz = models.CharField(max_length=250, null=True, blank=True, verbose_name="Lagerplatz")
    bestand = models.IntegerField(null=True, blank=True, verbose_name="Bestand")
    regal = models.CharField(max_length=250, null=True, blank=True, verbose_name="Regal")
    scanner = models.IntegerField(null=True, blank=True, verbose_name="Scanner")
    name = models.CharField(max_length=250, null=True, blank=True, verbose_name="Person")
    karton = models.CharField(max_length=250, null=True, blank=True, verbose_name="Karton")
    box = models.CharField(max_length=250, null=True, blank=True, verbose_name="Box")
    aufnahme_datum = models.CharField(max_length=250, null=True, blank=True, verbose_name="Aufnahme Datum")
    ignore_unique = models.CharField(max_length=250, null=True, blank=True, choices=IGNORE_CHOICES,
                                     verbose_name="Block")
    sku_instance = models.ForeignKey(Sku, null=True, blank=True, verbose_name="Sku Instanz",
                                     on_delete=models.SET_NULL)
    missing_amount = models.IntegerField(blank=True, null=True, verbose_name="Fehlender Bestand")
    product = models.ForeignKey(Product, blank=True, null=True, on_delete=models.SET_NULL)

    def get_absolute_url(self):
        return reverse("stock:detail", kwargs={'pk': self.id})

    def __str__(self):
        return str(self.ean_vollstaendig)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, hard_save=None, *args, **kwargs):
        product = self.get_product()
        if product is not None:
            self.product = product
        sku = self.get_sku()
        if sku is not None:
            self.sku_instance = sku
        if hard_save is None:
            if is_stock_reserved(self) > self.bestand:
                return
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False, hard_delete=None, *args, **kwargs):
        print(f"sdnfadsfndsajfndsa waaaaaarrummmm   +******")
        if hard_delete is None:
            if is_stock_reserved(self) > 0:
                print(f"NICHT GELÖSCHT!!!!")
                return
            print(f"GELÖSCHT")
        super().delete(*args, **kwargs)

    def clean(self):
        if self.lagerplatz is None:
            return

    def get_total_stocks(self, product=None):
        if self.product is not None:
            product = self.product

        if product is None:
            product = self.get_product()

        if product is None:
            if self.sku is not None and self.sku != "":
                total_from_sku = self.get_total_from_sku()
                if total_from_sku is not None:
                    return {"Gesamt": total_from_sku, "Neu": self.get_total_from_sku(state="Neu"),
                            "B": self.get_total_from_sku(state="B"), "C": self.get_total_from_sku(state="C"),
                            "D": self.get_total_from_sku(state="D"), "G": self.get_total_from_sku(state="G")
                            }
            if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
                total_from_ean = self.get_total_from_ean()
                if total_from_ean is not None:
                    return {"Gesamt": total_from_ean, "Neu": self.get_total_from_ean(state="Neu"),
                            "B": self.get_total_from_ean(state="B"), "C": self.get_total_from_ean(state="C"),
                            "D": self.get_total_from_ean(state="D"), "G": self.get_total_from_ean(state="G"),
                            }
            if self.title is not None and self.title != "":
                total_from_title = self.get_total_from_title()
                if total_from_title is not None:
                    return {"Gesamt": total_from_title, "Neu": self.get_total_from_title(state="Neu"),
                            "B": self.get_total_from_title(state="B"), "C": self.get_total_from_title(state="C"),
                            "D": self.get_total_from_title(state="D"), "G": self.get_total_from_title(state="G")
                            }

        total = self.get_total_from_all_products(product)

        return total

    def get_total_from_all_products(self, product):
        all_products = self.get_all_products(product)
        total = self.get_total(product=product)
        print(f"Syrien: {product.ean} - {total}")
        total = self.get_available_total_from_all_products(all_products, total)
        print(f"Marokko: {product.ean} - {total}")

        return total

    def get_total(self, product=None):

        if product is None:
            product = self.get_product()

        total = {}

        for state in self.states:
            total[state] = 0
        print(f"babfadbdfbd: {self.states}")

        all_products = self.get_all_products(product)

        if all_products is not None:
            for p in all_products:
                for sku in p.sku_set.all():
                    sku_string = sku.sku
                    sku_state = sku.state

                    if sku_state not in self.states:
                        self.states.append(sku_state)
                        total[sku_state] = 0

                    state_total = Stock.objects.filter(sku=sku_string).aggregate(Sum("bestand")).\
                        get("bestand__sum")

                    if state_total is not None:
                        if sku_state in total:
                            total[sku_state] += int(state_total)

        ean_stocks = None

        if product is not None:
            if product.ean is not None and product.ean != "":
                ean_stocks = Stock.objects.filter(ean_vollstaendig=product.ean)

        if ean_stocks is not None:
            for ean_stock in ean_stocks:
                if ean_stock.zustand in total:
                    total[ean_stock.zustand] += int(ean_stock.bestand)

        total["Gesamt"] = 0

        for state in self.states:
            total["Gesamt"] += total[state]

        return total

    def get_available_total_from_all_products(self, products, total):

        available_total = total.copy()

        if products is not None:
            for product in products:

                for sku in product.sku_set.all():
                    sku_string = sku.sku
                    sku_state = sku.state

                    if sku_state not in self.states:
                        self.states.append(sku_state)
                        total[sku_state] = 0

                    total_amount = 0

                    partial_products = PartialMissionProduct.objects.filter(
                        product_mission__product__sku__sku=sku_string, product_mission__state=sku_state)

                    for partial_product in partial_products:
                        total_amount += partial_product.missing_amount()

                    online_total = 0
                    print(f"sa {sku_string} {sku_state}")

                    online_missions_products = ProductMission.objects.filter(mission__is_online=True,
                                                                             product__sku__sku=sku_string,
                                                                             mission__online_picklist__completed__isnull
                                                                             =True, state=sku_state)

                    for mission_product in online_missions_products:
                        online_total += mission_product.amount

                    print(f"?? {online_total}")
                    print(f"subh assr: {online_missions_products} - {online_total}")

                    print(f"!! {total_amount}")

                    if total_amount is not None:
                        total_amount -= online_total
                        if int(total_amount) > 0:
                            available_total[sku_state] = f"{int(total[sku_state])-int(total_amount)}"
                        else:
                            available_total[sku_state] = f"{int(total[sku_state])+int(total_amount)}"

        available_total_gesamt = 0
        print(f"bandi: {self.states}")
        for state in self.states:
            total[state] = f"{available_total.get(state)}/{total.get(state)}"
            available_total_gesamt += int(available_total.get(state))

        total["Gesamt"] = f"{available_total_gesamt}/{total['Gesamt']}"

        return total

    def get_all_products(self, product):
        products = None
        if product is not None:
            if product.ean is not None and product.ean != "":
                products = Product.objects.filter(ean=product.ean)

        if product is not None and products is None:
            return [product]
        return products

    def get_sku(self):
        sku = None
        if self.sku is not None and self.sku != "":
            sku = Sku.objects.filter(sku=self.sku).first()

        if (self.ean_vollstaendig is not None and self.ean_vollstaendig != ""
                and self.zustand is not None and self.zustand != ""):
            sku = Sku.objects.filter(product__ean=self.ean_vollstaendig, state=self.zustand).first()
        return sku

    def get_product(self):
        product = None
        if self.sku is not None and self.sku != "":
            product = Product.objects.filter(sku__sku=self.sku).first()

        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            product = Product.objects.filter(ean=self.ean_vollstaendig).first()
        return product

    def get_total_from_sku(self, state=None):
        if state is None:
            total = Stock.objects.filter(sku=self.sku).aggregate(Sum("bestand"))["bestand__sum"]
        else:
            sku = None
            sku_number = re.findall('\d+', self.sku)
            if len(sku_number) > 0:
                sku = sku_number[0]
            total = Stock.objects.filter(sku=f"{state}{sku}").aggregate(Sum("bestand"))["bestand__sum"]
        if total is None:
            return "0"
        else:
            return total

    def get_total_from_ean(self, state=None):
        if state is None:
            total = Stock.objects.filter(ean_vollstaendig=self.ean_vollstaendig)\
                .aggregate(Sum("bestand"))["bestand__sum"]
        else:
            total = Stock.objects.filter(ean_vollstaendig=self.ean_vollstaendig, zustand=state)\
                .aggregate(Sum("bestand"))["bestand__sum"]

        if total is None:
            return "0"
        else:
            return total

    def get_total_from_title(self, state=None):
        if state is None:
            total = Stock.objects.filter(title=self.title).\
                aggregate(Sum("bestand"))["bestand__sum"]
        else:
            total = Stock.objects.filter(title=self.title, zustand=state)\
                .aggregate(Sum("bestand"))["bestand__sum"]

        if total is None:
            return "0"
        else:
            return total

    def get_total_from_product(self, product):

        result = {}
        all_skus = {}

        if product is not None:
            for sku in product.sku_set.all():
                all_skus[sku.sku] = sku

        for sku_string, sku_instance in all_skus.items():
            if sku_instance.state not in self.states:
                self.states.append(sku_instance.state)

            sku_total = Stock.objects.filter(sku=sku_string).aggregate(Sum("bestand")).get("bestand__sum")

            if sku_total is not None:
                result[sku_instance.state] = sku_total
            else:
                result[sku_instance.state] = "0"

        if product is not None:
            def add_ean_of_state_x_to_result(state, result):
                total_of_state = Stock.objects.filter(ean_vollstaendig=product.ean, zustand__iexact=state)\
                    .aggregate(Sum("bestand")).get("bestand__sum")

                if total_of_state is None:
                    total_of_state = 0

                if state in result:
                    result[state] = f'{int(result[state]) + int(total_of_state)}'
                else:
                    result[state] = total_of_state
                return result

            if product.ean is not None and product.ean != "":
                for state in self.states:
                    result = add_ean_of_state_x_to_result(state, result)

        total = 0
        for k, v in result.items():
            total += int(v)

        result["Gesamt"] = total
        return result

    def get_available_total_stocks(self, product=None):

        if self.product is not None:
            product = self.product

        if product is None or product == "":
            product = self.get_product()

        total = self.get_total(product=product)

        products = self.get_all_products(product)

        available_total = total.copy()

        if products is not None:
            for product in products:
                for sku in product.sku_set.all():
                    sku_string = sku.sku
                    sku_state = sku.state

                    if sku_state not in self.states:
                        self.states.append(sku_state)
                        total[sku_state] = 0

                    real_amount_total = PartialMissionProduct.objects.filter(
                        product_mission__product__sku__sku=sku_string, product_mission__state=sku_state
                    ).aggregate(Sum("amount")).get("amount__sum")

                    pick_list_total = 0

                    for pick_row in PickListProducts.objects.filter(product_mission__product__sku__sku=sku_string,
                                                                    product_mission__state=sku_state):
                        if pick_row.confirmed is not None and pick_row.confirmed != "":
                            pick_list_total += pick_row.amount_minus_missing_amount()

                    delivery_note_total = 0

                    for delivery_note_product in DeliveryNoteProductMission.objects\
                            .filter(product_mission__product__sku__sku=sku_string, product_mission__state=sku_state):
                        delivery_note_total += delivery_note_product.amount

                    if real_amount_total is not None and real_amount_total != "":
                        real_amount_total -= pick_list_total
                        if sku_state not in self.states:
                            total[sku_state] = 0
                        available_total[sku_state] = f"{int(total[sku_state])-int(real_amount_total)}"
                        available_total[sku_state] = f"{int(available_total[sku_state])+int(delivery_note_total)}"

                        # total["Gesamt"] -= f"{int(total['Gesamt'])}"

        available_total_gesamt = 0

        for state in self.states:
            available_total_gesamt += int(available_total.get(state))

        available_total["Gesamt"] = f"{available_total_gesamt}"

        return available_total

    def get_reserved_stocks(self):

        available_stocks = self.get_available_total_stocks()
        total_stocks = self.get_total()

        print(f"bababa: {available_stocks}")
        print(f"rafael: {total_stocks}")
        reserved_stocks = {}

        for state in self.states:
            reserved_stocks[state] = int(total_stocks.get(state))-int(available_stocks.get(state))
        reserved_stocks["Gesamt"] = int(total_stocks.get("Gesamt")) - int(available_stocks.get("Gesamt"))

        return reserved_stocks

    def get_available_stocks_of_total_stocks(self, product=None):
        total_stocks = self.get_total_stocks(product=product)
        return total_stocks

    def available_total_amount(self, state=None):
        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            if state is not None:
                total = Stock.objects.filter(ean_vollstaendig=str(self.ean_vollstaendig), zustand__iexact=state).\
                    aggregate(Sum('bestand'))
            else:
                total = Stock.objects.filter(ean_vollstaendig=str(self.ean_vollstaendig)).aggregate(Sum('bestand'))

            real_amounts = PartialMissionProduct.objects.filter(product_mission__product__ean=self.ean_vollstaendig)
            total_reserved = 0
            for real_amount in real_amounts:
                total_reserved += real_amount.real_amount

            total["bestand__sum"] -= total_reserved

        elif self.sku is not None and self.sku != "":
            if state is not None:
                total = Stock.objects.filter(sku=str(self.sku), zustand__iexact=state).aggregate(Sum('bestand'))
            else:
                total = Stock.objects.filter(sku=str(self.sku)).aggregate(Sum('bestand'))
        elif self.title is not None and self.title != "":
            if state is not None:
                total = Stock.objects.filter(title=str(self.title), zustand__iexact=state).aggregate(Sum('bestand'))
            else:
                total = Stock.objects.filter(title=str(self.title)).aggregate(Sum('bestand'))
            real_amounts = PartialMissionProduct.objects.filter(product_mission__product__title=self.title)
            total_reserved = 0
            for real_amount in real_amounts:
                total_reserved += real_amount.real_amount

            total["bestand__sum"] -= total_reserved
        else:
            return None
        total = {"bestand__sum": total["bestand__sum"]}

        return total["bestand__sum"]

    def get_state(self):
        if self.zustand is not None and self.zustand != "":
            return self.zustand

        if self.product is not None:
            return self.product.get_state_from_sku(self.sku)

    def get_real_stock(self):
        total = 0
        stocks = None
        if self.sku is not None:
            sku = Sku.objects.filter(sku=self.sku).first()
            if sku is not None:
                sku_string = sku.sku
                stocks = Stock.objects.filter(sku=sku_string)

        if self.ean_vollstaendig is not None and self.zustand is not None:
            stocks = Stock.objects.filter(ean_vollstaendig=self.ean_vollstaendig, zustand=self.zustand)

        if stocks is not None:
            total = stocks.aggregate(Sum("bestand"))["bestand__sum"]

        online_total = 0

        query_condition = Q(Q(mission__is_online=True, mission__online_picklist__completed__isnull=True)
                            & Q(Q(product__ean=self.ean_vollstaendig, state=self.zustand) |
                                Q(product__sku__sku=self.sku)))

        online_missions_products = ProductMission.objects.filter(query_condition).distinct("pk")

        for mission_product in online_missions_products:
            online_total += mission_product.amount

        print(f"?? {online_total}")

        if total is not None:
            total -= online_total
        return total or 0


class Stockdocument(models.Model):
    document = models.FileField(upload_to='documents/', null=True, blank=False)
    uploaded_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse("stock:documentdetail", kwargs={"pk": self.id})


class Position(models.Model):
    name = models.CharField(blank=True, null=False, max_length=250, verbose_name="Position")
    prefix = models.CharField(blank=True, null=False, max_length=250, verbose_name="Prefix")
    shelf = models.IntegerField(blank=True, null=False, verbose_name="Regal")
    level = models.IntegerField(blank=True, null=False, verbose_name="Ebene")
    column = models.IntegerField(blank=True, null=False, verbose_name="Spalte")

    def __str__(self):
        return self.position

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.name is None or self.name == "":
            self.name = self.position
        super().save()

    @property
    def position(self):
        if str(self.level).isdigit():
            level = '%03d' % (int(self.level),)
        else:
            level = self.level
        if str(self.column).isdigit():
            column = '%03d' % (int(self.column),)
        else:
            column = self.column

        position = f"{self.prefix}{self.shelf}-{level}-{column}"

        if all(char.isalpha() or char.isspace() or char == "-" for char in position):
            return self.prefix

        return position

    class Meta:
        ordering = ["prefix", "shelf", "level", "column"]
