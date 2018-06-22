from django.db import models
import datetime
from django.core.urlresolvers import reverse
from django.db.models import Q

from adress.models import Adress
from customer.models import Customer
from product.models import Product
from datetime import date
from order.models import terms_of_delivery_choices, terms_of_payment_choices, shipping_choices
from django.db.models import Max
from django.core.exceptions import ValidationError

CHOICES = (
    (None, "----"),
    (True, "Ja"),
    (False, "Nein")
)


# Create your models here.
class Mission(models.Model):
    mission_number = models.CharField(max_length=200, blank=True, verbose_name="Auftragsnummer")
    delivery_date = models.DateField(default=datetime.date.today, verbose_name="Lieferdatum")
    status = models.CharField(max_length=200, null=True, blank=True, default="OFFEN", verbose_name="Status")
    products = models.ManyToManyField(Product, through="ProductMission")
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
                                         on_delete=models.SET_NULL)
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    shipping = models.CharField(choices=shipping_choices, blank=True, null=True, max_length=200,
                                verbose_name="Spedition")
    shipping_number_of_pieces = models.IntegerField(blank=True, null=True, verbose_name="Stückzahl Transport")
    shipping_costs = models.FloatField(blank=True, null=True, max_length=200, verbose_name="Transportkosten")
    confirmed = models.NullBooleanField(choices=CHOICES, verbose_name="Bestätigt")

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


class ProductMission(models.Model):
    class Meta:
        ordering = ['pk']

    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Artikel")
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, unique=False, blank=False, null=False,
                                verbose_name="Auftrag")
    state = models.CharField(max_length=200, verbose_name="Zustand", null=True, blank=True)
    amount = models.IntegerField(null=False, blank=False, default=0, verbose_name="Menge")
    missing_amount = models.IntegerField(null=True, blank=True, verbose_name="Fehlende Menge")
    netto_price = models.FloatField(null=True, blank=True, verbose_name="Einzelpreis (Netto)")
    confirmed = models.NullBooleanField(verbose_name="Bestätigt")

    def __str__(self):
        return str(self.product) + " : " + str(self.mission) + " : " + str(self.amount)

    @property
    def real_amount(self):
        if self.amount and self.missing_amount:
            return self.amount - self.missing_amount
        else:
            return self.amount

    def get_ean_or_sku(self):
        ean_or_sku = None
        print(f"BUS: {ean_or_sku}")

        if self.product.ean is not None and self.product.ean != "":
            ean_or_sku = self.product.ean
        else:
            sku_instance = self.product.sku_set.filter(state=self.state).first()
            if sku_instance is not None:
                ean_or_sku = sku_instance.sku
        print(f"BUS: {ean_or_sku}")
        return ean_or_sku

    # def save(self, *args, **kwargs):
    #     self.full_clean()
    #     super().save(*args, **kwargs)


class RealAmountModelManager(models.Manager):
    def bulk_create(self, objs, batch_size=None):
        super().bulk_create(objs)
        for obj in objs:
            obj.save()


class Delivery(models.Model):
    mission = models.ForeignKey(Mission, null=True, blank=True)


class GoodsIssue(models.Model):
    delivery = models.ForeignKey("mission.Delivery", null=True, blank=True)

    scan_id = models.CharField(max_length=200, blank=True, null=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.scan_id is None or self.scan_id == "":
            self.scan_id = f"PK{self.pk+1}"
        super().save()


class PickList(models.Model):
    delivery = models.ForeignKey("mission.Delivery", null=True, blank=True)
    pick_id = models.CharField(max_length=200, blank=True, null=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.pick_id is None or self.pick_id == "":
            self.pick_id = f"PK{self.pk+1}"
        super().save()


class PackingList(models.Model):
    delivery = models.ForeignKey("mission.Delivery", null=True, blank=True)
    packing_id = models.CharField(max_length=200, blank=True, null=True)

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

    def real_amount(self):
        amount = self.amount
        if self.goods_issue is not None and self.goods_issue != "":
            for delivery_note in self.goods_issue.deliverynote_set.all():
                for delivery_note_product in delivery_note.deliverynoteproductmission_set\
                        .filter(product_mission__exact=self.delivery_mission_product.product_mission):
                    amount -= delivery_note_product.amount
        return amount

    def scan_amount(self):
        amount = 0
        picklist = self.packing_list.delivery.picklist_set.first()

        if picklist is not None and picklist != "":
            for pick_row in picklist.picklistproducts_set.filter(Q(Q(confirmed=True) | Q(confirmed=False))
                                                                 & Q(product_mission=self.product_mission)):
                amount += pick_row.amount_minus_missing_amount()
        return amount


class IgnoreStocksPickList(models.Model):
    delivery = models.ForeignKey("mission.Delivery", null=True, blank=True)
    product_mission = models.ForeignKey(ProductMission, null=True, blank=True)
    position = models.CharField(verbose_name="Lagerplatz", null=True, blank=True, max_length=200)


class PickListProducts(models.Model):
    pick_list = models.ForeignKey(PickList, null=True, blank=True)
    product_mission = models.ForeignKey(ProductMission, null=True, blank=True)
    amount = models.IntegerField(verbose_name="Menge", null=True, blank=True)
    position = models.CharField(verbose_name="Lagerplatz", null=True, blank=True, max_length=200)
    confirmed = models.NullBooleanField(verbose_name="Bestätigt", blank=True, null=True)
    missing_amount = models.IntegerField(verbose_name="Fehlende Menge", blank=True, null=True)

    def amount_minus_missing_amount(self):
        if self.missing_amount is not None and self.missing_amount != "":
            return int(self.amount) - int(self.missing_amount)
        return self.amount


class GoodsIssueDeliveryMissionProduct(models.Model):
    goods_issue = models.ForeignKey("mission.GoodsIssue", null=True, blank=True)
    delivery_mission_product = models.ForeignKey("mission.DeliveryMissionProduct", null=True, blank=True)
    amount = models.IntegerField(blank=True, null=True, verbose_name="Menge", default=0)
    missing_amount = models.IntegerField(null=True, blank=True, verbose_name="Fehlende Menge", default=0)
    confirmed = models.NullBooleanField(verbose_name="Bestätigt", blank=True, null=True)

    def amount_minus_missing_amount(self):
        if self.missing_amount is None:
            return self.scan_amount()
        return self.scan_amount()-self.missing_amount

    def real_amount(self):
        amount = self.amount
        if self.goods_issue is not None and self.goods_issue != "":
            for delivery_note in self.goods_issue.deliverynote_set.all():
                for delivery_note_product in delivery_note.deliverynoteproductmission_set\
                        .filter(product_mission__exact=self.delivery_mission_product.product_mission):
                    amount -= delivery_note_product.amount
        return amount

    def scan_amount(self):
        amount = 0
        picklist = self.goods_issue.delivery.picklist_set.first()
        if picklist is not None and picklist != "":
            for pick_row in picklist.picklistproducts_set.filter(Q(Q(confirmed=True) | Q(confirmed=False))
                                                                 & Q(product_mission=
                                                                     self.delivery_mission_product.product_mission)):
                amount += pick_row.amount_minus_missing_amount()
        return amount


class DeliveryMissionProduct(models.Model):
    delivery = models.ForeignKey(Delivery, null=True, blank=True)
    product_mission = models.ForeignKey(ProductMission, null=True, blank=True)
    amount = models.IntegerField(blank=True, null=True)

    def real_amount(self):
        amount = 0
        delivery_notes_products = DeliveryNoteProductMission.objects.\
            filter(product_mission=self.product_mission, delivery_note__delivery=self.delivery)

        if delivery_notes_products.count() > 0:
            for row in delivery_notes_products:
                amount += row.amount
        return amount

    def missing_amount(self):
        return self.amount-self.real_amount()


class RealAmount(models.Model):
    product_mission = models.ForeignKey(ProductMission)
    real_amount = models.IntegerField(blank=True, null=True)
    missing_amount = models.IntegerField(null=True, blank=True, verbose_name="Fehlende Menge")
    billing = models.ForeignKey("mission.Billing", blank=True, null=True)
    delivery_note = models.ForeignKey("mission.DeliveryNote", blank=True, null=True)
    confirmed = models.NullBooleanField(choices=CHOICES, verbose_name="Bestätigt")

    @property
    def real_amount_minus_missing_amount(self):
        if self.missing_amount is None:
            return self.real_amount
        return self.real_amount-self.missing_amount

    def get_delivery_note_amount(self):
        amount = self.real_amount-self.missing_amount
        for delivery_note in self.billing.deliverynote_set.all():
            for product in delivery_note.deliverynoteproductmission_set.all():
                if product.product_mission.pk == self.product_mission.pk:
                    amount -= product.amount


class Billing(models.Model):
    billing_number = models.CharField(max_length=200, null=True, blank=True)
    delivery = models.ForeignKey("mission.Delivery", null=True, blank=True)

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


class DeliveryNote(models.Model):
    class Meta:
        ordering = ['pk']

    delivery_note_number = models.CharField(max_length=200, null=True, blank=True)
    delivery = models.ForeignKey("mission.Delivery", null=True, blank=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.delivery_note_number is None or self.delivery_note_number == "":
            self.delivery_note_number = f"LS{self.pk+1}"
        super().save()


class DeliveryNoteProductMission(models.Model):
    product_mission = models.ForeignKey(ProductMission, null=True, blank=True)
    amount = models.IntegerField(blank=True, null=True)
    delivery_note = models.ForeignKey("mission.DeliveryNote", blank=True, null=True)
    billing = models.ForeignKey("mission.Billing", blank=True, null=True)
