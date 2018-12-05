from django.contrib.postgres.aggregates import ArrayAgg
from django.db import models
import datetime
from django.core.urlresolvers import reverse
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery

from adress.models import Adress
from customer.models import Customer
from product.models import Product
from datetime import date
from order.models import terms_of_delivery_choices, terms_of_payment_choices, shipping_choices
from django.db.models import Max
from django.core.exceptions import ValidationError
from mission.managers import MissionObjectManager
from online.models import Channel
import django
from django.contrib.auth import get_user_model
from django.db.models import F, Q, Sum, Case, When, Count

from sku.models import Sku
from utils.models.base import ModelBase

CHOICES = (
    (None, "----"),
    (True, "Ja"),
    (False, "Nein")
)

online_shipping_choices = (
    ("DHL", "DHL"),
    ("DPD", "DPD"),
)


# Create your models here.
class Mission(models.Model):
    mission_number = models.CharField(max_length=200, blank=True, verbose_name="Auftragsnummer")
    delivery_date = models.DateField(default=datetime.date.today, verbose_name="Lieferdatum")
    delivery_date_from = models.DateField(null=True, blank=True, verbose_name="Lieferdatum von")
    delivery_date_to = models.DateField(null=True, blank=True, verbose_name="Lieferdatum bis")
    ship_date_from = models.DateField(null=True, blank=True, verbose_name="Versanddatum von")
    ship_date_to = models.DateField(null=True, blank=True, verbose_name="Versanddatum bis")
    status = models.CharField(max_length=200, null=True, blank=True, default="OFFEN", verbose_name="Status")
    channel = models.ForeignKey(Channel, null=True, blank=True, verbose_name="Channel")
    skus = models.ManyToManyField(Sku, through="ProductMission")
    customer = models.ForeignKey(Customer, null=True, blank=True, related_name='mission', verbose_name="Kunde",
                                 on_delete=models.SET_NULL)
    customer_order_number = models.CharField(max_length=200, null=True, blank=True,
                                             verbose_name="Bestellnummer vom Kunden")

    billing_number = models.CharField(max_length=200, blank=True, verbose_name="Rechnungsnummer")
    delivery_note_number = models.CharField(max_length=200, blank=True, verbose_name="Lieferscheinnummer")

    terms_of_payment = models.CharField(choices=terms_of_payment_choices, blank=True, null=True, max_length=200,
                                        verbose_name="Zahlungsbedingung")
    terms_of_delivery = models.CharField(choices=terms_of_delivery_choices, blank=True, null=True, max_length=200,
                                         verbose_name="Lieferkonditionen")
    delivery_address = models.ForeignKey(Adress, null=True, blank=True, verbose_name="Lieferadresse",
                                         on_delete=models.SET_NULL, related_name="delivery")
    billing_address = models.ForeignKey(Adress, null=True, blank=True, verbose_name="Rechnungsadresse",
                                        on_delete=models.SET_NULL, related_name="billing")
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified_date = models.DateTimeField(auto_now=True, null=True, blank=True)

    confirmed = models.NullBooleanField(choices=CHOICES, verbose_name="Bestätigt")
    channel_order_id = models.CharField(max_length=200, null=True, blank=True, verbose_name="Fremd ID")

    is_amazon_fba = models.NullBooleanField(null=True, blank=True, verbose_name="Fulfillment")

    is_amazon = models.NullBooleanField(null=True, blank=True, verbose_name="Amazon")

    is_ebay = models.NullBooleanField(null=True, blank=True, verbose_name="Ebay")

    purchased_date = models.DateTimeField(null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)

    tracking_number = models.CharField(null=True, blank=True, verbose_name="Tracking Nummer", max_length=200)
    shipping = models.CharField(choices=online_shipping_choices, blank=True, null=True, max_length=200,
                                verbose_name="Transportdienstleister")

    label_pdf = models.FileField(null=True, blank=True, upload_to="labels/")

    online_picklist = models.ForeignKey("mission.PickList", null=True, blank=True, verbose_name="Online Pickauftrag",
                                        on_delete=django.db.models.deletion.SET_NULL)

    online_transport_cost = models.FloatField(null=True, blank=True, verbose_name="Transportkosten")

    online_business_account = models.ForeignKey("disposition.BusinessAccount", null=True, blank=True,
                                                verbose_name="Geschäftskonto Transportdienstleister")

    online_transport_service = models.ForeignKey("disposition.TransportService", null=True, blank=True)

    is_online = models.NullBooleanField(choices=CHOICES, verbose_name="Onlinehandel")

    shipped = models.NullBooleanField(verbose_name="Versendet")

    not_matchable = models.NullBooleanField(verbose_name="Nicht matchbar")

    none_sku_products_amount = models.IntegerField(null=True, blank=True, verbose_name="Anzahl Artikel ohne SKU")

    objects = MissionObjectManager()

    def get_online_status(self, mission_products, mission_products_without_match):
        if self.not_matchable is True:
            if mission_products.count() > 0:
                for mission_product in mission_products:
                    if mission_product.sku is not None and mission_product.sku.product.ean in [None, ""]:
                        return "Artikel ohne EAN"
            if mission_products_without_match.count() > 0 or self.none_sku_products_amount is not None:
                return "Artikel nicht zugeordnet"

        if self.none_sku_products_amount is not None:
            return "Artikel nicht zugeordnet"

        if mission_products.count() == 0:
            return "Artikel nicht zugeordnet"

        if self.status == "Manuell":
            return "Manuell"

        if self.online_picklist is not None:
            if self.online_picklist.completed is True and self.tracking_number is not None:
                return "Verpackt"

            pick_order = self.online_picklist.pick_order
            if pick_order is not None:
                packing_station = pick_order.packingstation_set.first()
                if packing_station is None:
                    return "am Picken"
                else:
                    return f"auf Station {packing_station.station_id}"
        return "Offen"

    @property
    def difference_delivery_date_today(self):
        today = datetime.date.today()
        if self.delivery_date is not None:
            difference_days = today-self.delivery_date
            return difference_days.days

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_confirmed = self.confirmed

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.mission_number is None or self.mission_number == "":
            self.mission_number = f"A{self.pk+1}"
        if self.is_online is None:
            self.status = get_status(self)
        else:
            missions_products = self.productmission_set.all()
            mission_products_without_match = missions_products.filter(no_match_sku__isnull=False)
            if (missions_products.count() > 0 and mission_products_without_match.count() == 0 and
                    self.none_sku_products_amount is None):
                self.not_matchable = None
            else:
                self.not_matchable = True
            print(f"gamery: {mission_products_without_match}")
            print(f"2: {mission_products_without_match.count()}")
            self.status = self.get_online_status(missions_products, mission_products_without_match)
        super().save()

    # def save(self, *args, **kwargs):
    #     if self.mission_number == "":
    #         today = date.today().strftime('%d%m%y')
    #         count = Mission.objects.filter(mission_number__icontains=today).count()+1
    #         self.mission_number = f"A{today}" + '%03d' % count
    #     super().save(force_insert=False, force_update=False, *args, **kwargs)

    def __str__(self):
        return self.mission_number

    def get_absolute_url(self):
        return reverse("mission:detail", kwargs={"pk": self.id})


class ProductMissionQuerySet(models.QuerySet):
    def get_online_stocks(self):
        from stock.models import Stock
        from configuration.models import OnlinePositionPrefix
        online_prefixes = OnlinePositionPrefix.objects.all()
        online_prefixes_condition = Q()
        for prefix in online_prefixes:
            online_prefixes_condition |= Q(stock__lagerplatz__istartswith=prefix.prefix)

        stock_condition = Q(Q(stock__sku_instance__product=F("product"),
                              stock__sku_instance__state=F("state")) |
                            Q(stock__ean_vollstaendig=F("product__ean"),
                              stock__zustand=F("state")))

        subquery_sku = Sku.objects.filter(product=OuterRef("sku__product"), state=OuterRef("sku__state")).annotate(
            total=Sum(Case(When(stock_condition, then="stock__bestand"), default=0))).annotate(
            online_total=Sum(Case(When(Q(stock_condition & online_prefixes_condition),
                                       then="stock__bestand"), default=0)))[:1]

        subquery_mission_total = Sku.objects.filter(sku=OuterRef("sku__sku")).annotate(
            mission_total=Sum(Case(When(productmission__mission__is_online=True,
                                        productmission__mission__online_picklist__completed__isnull=True,
                                        then="productmission__amount"), default=0)))[:1]

        subquery_picklists_total = ProductMission.objects.filter(pk=OuterRef("pk")).annotate(
            picklists_total=Sum(Case(When(sku__productmission__sku=F("sku"),
                                          sku__productmission__picklistproducts__pick_list__completed__isnull=True,
                                          sku__productmission__mission__is_online=True,
                                          then="sku__productmission__picklistproducts__amount"), default=0)))[:1]

        return self.all().annotate(
            total=Subquery(subquery_sku.values("total"), output_field=models.IntegerField())).annotate(
            mission_total=Subquery(subquery_mission_total.values("mission_total"),
                                   output_field=models.IntegerField())).annotate(
            available_total=F("total")-F("mission_total")).annotate(
            online_total=Subquery(subquery_sku.values("online_total"), output_field=models.IntegerField())).annotate(
            refill_total=F("mission_total")-F("online_total")).annotate(
            picklists_total=Subquery(subquery_picklists_total.values("picklists_total")))


class ProductMissionManager(models.Manager):
    def get_queryset(self):
        return ProductMissionQuerySet(self.model, using=self._db)  # Important!


class ProductMission(models.Model):
    class Meta:
        ordering = ['pk']

    objects = ProductMissionManager()

    sku = models.ForeignKey(Sku, on_delete=models.deletion.SET_NULL, verbose_name="Sku", null=True)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, unique=False, blank=False, null=False,
                                verbose_name="Auftrag")
    state = models.CharField(max_length=200, verbose_name="Zustand", null=True, blank=True)
    amount = models.IntegerField(null=False, blank=False, default=0, verbose_name="Menge")
    online_shipped_amount = models.IntegerField(null=False, blank=False, default=0, verbose_name="Versendete Menge")
    missing_amount = models.IntegerField(null=True, blank=True, verbose_name="Fehlende Menge")
    netto_price = models.FloatField(null=True, blank=True, verbose_name="Einzelpreis (Netto)")
    brutto_price = models.FloatField(null=True, blank=True, verbose_name="Einzelpreis (Brutto)")
    shipping_price = models.FloatField(null=True, blank=True, verbose_name="Versandkosten")
    discount = models.FloatField(null=True, blank=True, verbose_name="Rabatt")
    shipping_discount = models.FloatField(null=True, blank=True, verbose_name="Rabatt für Versand")
    confirmed = models.NullBooleanField(verbose_name="Bestätigt")
    no_match_sku = models.CharField(max_length=200, null=True, blank=True)
    online_identifier = models.CharField(max_length=500, null=True, blank=True)  # Amazon order-item-id zb
    online_description = models.TextField(null=True, blank=True, verbose_name="Online Beschreibung")

    @property
    def real_amount(self):
        if self.amount and self.missing_amount:
            return self.amount - self.missing_amount
        else:
            return self.amount

    def get_ean_or_sku(self):
        ean_or_sku = None

        if self.sku.product.ean is not None and self.sku.product.ean != "":
            ean_or_sku = self.sku.product.ean
        else:
            ean_or_sku = self.sku.sku
        return ean_or_sku

    # def save(self, *args, **kwargs):
    #     self.full_clean()
    #     super().save(*args, **kwargs)


class RealAmountModelManager(models.Manager):
    def bulk_create(self, objs, batch_size=None):
        super().bulk_create(objs)


class Partial(models.Model):
    class Meta:
        ordering = ["-pk"]

    mission = models.ForeignKey(Mission, null=True, blank=True)


class PickOrder(models.Model):
    pick_order_id = models.CharField(max_length=200, blank=True, null=True, verbose_name="Pickauftrags ID")
    user = models.ForeignKey(get_user_model(), on_delete=models.deletion.SET_NULL, null=True, blank=True)
    completed = models.NullBooleanField(null=True, blank=True, verbose_name="Erledigt")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save()
        if self.pick_order_id is None or self.pick_order_id == "":
            self.pick_order_id = f"PO{self.pk}"
        super().save()


class PickList(models.Model):
    partial = models.ForeignKey("mission.Partial", null=True, blank=True)
    pick_id = models.CharField(max_length=200, blank=True, null=True, verbose_name="Pick ID")
    delivery = models.ForeignKey("mission.Delivery", null=True, blank=True)
    pick_order = models.ForeignKey(PickOrder, null=True, blank=True)
    completed = models.NullBooleanField(null=True, blank=True, verbose_name="Erledigt")
    online_delivery_note = models.ForeignKey("mission.DeliveryNote", null=True, blank=True,
                                             on_delete=django.db.models.deletion.SET_NULL)
    online_billing = models.ForeignKey("mission.Billing", null=True, blank=True,
                                       on_delete=django.db.models.deletion.SET_NULL)
    note = models.CharField(max_length=400, blank=True, null=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.pick_id is None or self.pick_id == "":
            self.pick_id = f"PK{self.pk+1}"
        super().save()


class PackingStation(models.Model):
    class Meta:
        unique_together = ('station_number', 'prefix')
        ordering = ("prefix", "station_number")

    station_id = models.CharField(null=True, blank=True, max_length=200)
    prefix = models.CharField(null=True, blank=True, max_length=200)
    station_number = models.IntegerField(null=True, blank=True, verbose_name="Stationsnummer")
    pickorder = models.ForeignKey("mission.PickOrder", null=True, blank=True, on_delete=models.deletion.SET_NULL)
    user = models.ForeignKey(get_user_model(), on_delete=models.deletion.SET_NULL, null=True, blank=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.station_id is None or self.station_id == "":
            if self.prefix is not None:
                self.station_id = f"{self.prefix}{self.station_number}"
            else:
                self.station_id = f"PS{self.pk}"
        super().save()


class PackingList(models.Model):
    partial = models.ForeignKey("mission.Partial", null=True, blank=True)
    picklist = models.ForeignKey("mission.PickList", null=True, blank=True)
    packing_id = models.CharField(max_length=200, blank=True, null=True, verbose_name="Verpacker ID")

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.packing_id is None or self.packing_id == "":
            self.packing_id = f"VR{self.pk+1}"
        super().save()


class PackingListProduct(models.Model):
    packing_list = models.ForeignKey("mission.PackingList", null=True, blank=True)
    product_mission = models.ForeignKey("mission.ProductMission", null=True, blank=True)
    amount = models.IntegerField(blank=True, null=True, verbose_name="Menge", default=0)
    missing_amount = models.IntegerField(null=True, blank=True, verbose_name="Fehlende Menge", default=0)
    confirmed = models.NullBooleanField(verbose_name="Bestätigt", blank=True, null=True)

    def amount_minus_missing_amount(self):
        if self.missing_amount is None:
            return self.scan_amount()
        return self.scan_amount()-self.missing_amount

    def scan_amount(self):
        amount = 0
        picklist = self.packing_list.partial.picklist_set.first()

        if picklist is not None and picklist != "":
            for pick_row in picklist.picklistproducts_set.filter(Q(Q(confirmed=True) | Q(confirmed=False))
                                                                 & Q(product_mission=self.product_mission)):
                amount += pick_row.amount_minus_missing_amount()
        return amount


class IgnoreStocksPickList(models.Model):
    partial = models.ForeignKey("mission.Partial", null=True, blank=True)

    product_mission = models.ForeignKey(ProductMission, null=True, blank=True)
    position = models.CharField(verbose_name="Lagerplatz", null=True, blank=True, max_length=200)


class PickListProductsManager(models.Manager):
    def get_stock_reserved_total(self, stock):
        from stock.models import Stock
        if stock.pk is not None:
            old_stock = Stock.objects.get(pk=stock.pk)  # sonst gibt er den stock der nicht gespeichert wurde
            sku = None
            state = None
            sku_instance = old_stock.sku_instance
            if sku_instance is not None:
                sku = sku_instance.sku
                state = sku_instance.state
                print(f"omg: {sku} {state} - {stock.lagerplatz} - {old_stock.ean_vollstaendig} - {old_stock.zustand}")
            return self.filter(
                Q(Q(product_mission__sku__product__ean=old_stock.ean_vollstaendig,
                    product_mission__sku__state=old_stock.zustand) |
                  Q(product_mission__sku__state__iexact=state, product_mission__sku__product=sku_instance.product))
                & Q(Q(Q(pick_list__completed__isnull=True) & Q(pick_list__isnull=False)),
                    position=old_stock.lagerplatz)).aggregate(total=Sum("amount"))


class PickListProducts(models.Model):
    pick_list = models.ForeignKey(PickList, null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL)
    product_mission = models.ForeignKey(ProductMission, null=True, blank=True)
    amount = models.IntegerField(verbose_name="Menge", null=True, blank=True)
    position = models.CharField(verbose_name="Lagerplatz", null=True, blank=True, max_length=200)
    confirmed = models.NullBooleanField(verbose_name="Bestätigt", blank=True, null=True)
    picked = models.NullBooleanField(verbose_name="Gepickt", blank=True, null=True)
    missing_amount = models.IntegerField(verbose_name="Fehlende Menge", blank=True, null=True)
    confirmed_amount = models.IntegerField(verbose_name="Bestätigte Menge", null=True, blank=True)

    objects = PickListProductsManager()

    def amount_minus_missing_amount(self):
        if self.missing_amount is not None and self.missing_amount != "":
            return int(self.amount) - int(self.missing_amount)
        return self.amount


class PartialMissionProduct(models.Model):
    partial = models.ForeignKey("mission.Partial", null=True, blank=True)

    product_mission = models.ForeignKey(ProductMission, null=True, blank=True)
    amount = models.IntegerField(blank=True, null=True)

    def real_amount(self):
        amount = 0
        delivery_notes_products = DeliveryNoteProductMission.objects.\
            filter(product_mission=self.product_mission, delivery_note__delivery__partial=self.partial)

        if delivery_notes_products.count() > 0:
            for row in delivery_notes_products:
                amount += row.amount
        return amount

    def missing_amount(self):
        return self.amount-self.real_amount()


class Delivery(models.Model):
    delivery_id = models.CharField(max_length=200, blank=True, null=True)
    partial = models.ForeignKey("mission.Partial", null=True, blank=True)
    billing = models.ForeignKey("mission.Billing", null=True, blank=True)
    delivery_note = models.ForeignKey("mission.DeliveryNote", null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True, verbose_name="Lieferdatum")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save()
        if self.delivery_id is None or self.delivery_id == "":
            self.delivery_id = f"LG{self.pk+1}"
        super().save()

    def get_delivery_date(self):
        return self.delivery_date

    @property
    def difference_delivery_date_today(self):
        today = datetime.date.today()
        if self.delivery_date is not None:
            difference_days = today-self.delivery_date
            return difference_days.days


class DeliveryProduct(models.Model):
    delivery = models.ForeignKey(Delivery, null=True, blank=True)
    product_mission = models.ForeignKey(ProductMission, null=True, blank=True)
    amount = models.IntegerField(verbose_name="Menge", null=True, blank=True)


class Billing(ModelBase):
    class Meta:
        ordering = ['pk']

    billing_number = models.CharField(max_length=200, null=True, blank=True)

    delivery_date = models.DateField(null=True, blank=True, verbose_name="Lieferdatum")

    transport_service = models.CharField(choices=shipping_choices, blank=False, null=True, max_length=200,
                                         verbose_name="Transportdienstleister")
    shipping_number_of_pieces = models.IntegerField(blank=False, null=True, verbose_name="Stückzahl Transport")
    shipping_costs = models.FloatField(blank=False, null=True, max_length=200, verbose_name="Transportkosten")

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.billing_number is None or self.billing_number == "":
            self.billing_number = f"RG{self.pk+1}"
        super().save()


class BillingProductMissionManager(models.Manager):
    def bulk_create(self, objs, batch_size=None):
        super().bulk_create(objs)
        obj = objs[len(objs)-1]
        obj.product_mission.mission.status = get_status(obj.product_mission.mission)
        obj.product_mission.mission.save()


class BillingProductMission(models.Model):
    product_mission = models.ForeignKey(ProductMission, null=True, blank=True)

    amount = models.IntegerField(blank=True, null=True)
    billing = models.ForeignKey("mission.Billing", blank=True, null=True)

    objects = BillingProductMissionManager()


class DeliveryNote(ModelBase):
    class Meta:
        ordering = ['pk']

    delivery_note_number = models.CharField(max_length=200, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True, verbose_name="Lieferdatum")

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.delivery_note_number is None or self.delivery_note_number == "":
            self.delivery_note_number = f"LS{self.pk+1}"
        super().save()


class Truck(models.Model):
    class Meta:
        ordering = ["pk"]

    truck_id = models.CharField(null=True, blank=True, max_length=200)
    outgoing = models.NullBooleanField(blank=False)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.truck_id is None or self.truck_id == "":
            self.truck_id = f"LKW{self.pk}"
        super().save()


class DeliveryNoteProductMissionManager(models.Manager):
    def bulk_create(self, objs, batch_size=None):
        super().bulk_create(objs)
        obj = objs[len(objs)-1]
        obj.product_mission.mission.status = get_status(obj.product_mission.mission)
        obj.product_mission.mission.save()


class DeliveryNoteProductMission(models.Model):
    product_mission = models.ForeignKey(ProductMission, null=True, blank=True)

    amount = models.IntegerField(blank=True, null=True)
    delivery_note = models.ForeignKey("mission.DeliveryNote", blank=True, null=True)
    billing = models.ForeignKey("mission.Billing", blank=True, null=True)

    objects = DeliveryNoteProductMissionManager()


def get_status(mission):
    mission_products = mission.productmission_set.all()
    products_count = mission_products.count()

    if products_count == 0:
        return "OFFEN"
    else:
        partials = mission.partial_set.all()

        if partials.count() > 0:
            finished = True
            for mission_product in mission_products:
                sent_amount_sum = 0

                for partial_product in PartialMissionProduct.objects.filter(product_mission=mission_product):
                    sent_amount_sum += partial_product.real_amount()
                print(f"LIMIT: {mission_product.amount} - {sent_amount_sum}")
                if int(sent_amount_sum) != int(mission_product.amount):
                    finished = False
                    break
            if finished is True:
                return "BEENDET"
            else:
                return "IN BEARBEITUNG"
        else:
            # HIER WEITER MACHEN
            return "OFFEN"
