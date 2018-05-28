from django.db import models
import datetime
from django.core.urlresolvers import reverse

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

    def save(self, *args, **kwargs):
        # if self.__original_confirmed != self.confirmed:
        #     if self.confirmed is True:
        #             self.status = "PICKBEREIT"
        #     elif self.confirmed is False:
        #         self.status = "AUSSTEHEND"

        if self.mission_number == "":
            today = date.today().strftime('%d%m%y')
            count = Mission.objects.filter(mission_number__icontains=today).count()+1
            self.mission_number = f"A{today}" + '%03d' % count
        super().save(force_insert=False, force_update=False, *args, **kwargs)

    def __str__(self):
        return self.mission_number

    def get_absolute_url(self):
        return reverse("mission:detail", kwargs={"pk": self.id})


class ProductMission(models.Model):
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


class Billing(models.Model):
    billing_number = models.CharField(max_length=200, null=True, blank=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.billing_number is None or self.billing_number == "":
            self.billing_number = f"RG{self.pk+1}"
        super().save()


class DeliveryNote(models.Model):
    delivery_note_number = models.CharField(max_length=200, null=True, blank=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.delivery_note_number is None or self.delivery_note_number == "":
            self.delivery_note_number = f"LS{self.pk+1}"
        super().save()
