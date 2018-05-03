from django.db import models
import datetime
from django.core.urlresolvers import reverse

from adress.models import Adress
from customer.models import Customer
from product.models import Product
from datetime import date
from order.models import terms_of_delivery_choices, terms_of_payment_choices
from django.db.models import Max


# Create your models here.
class Mission(models.Model):
    mission_number = models.CharField(max_length=200, blank=True, verbose_name="Auftragsnummer")
    delivery_date = models.DateField(default=datetime.date.today, verbose_name="Lieferdatum")
    status = models.CharField(max_length=200, null=True, blank=True, default="OFFEN", verbose_name="Status")
    products = models.ManyToManyField(Product, through="ProductMission")
    customer = models.ForeignKey(Customer, null=True, blank=True, related_name='mission', verbose_name="Kunde")
    billing_number = models.CharField(max_length=200, blank=True, verbose_name="Rechnungsnummer")
    CHOICES = (
        (None, "----"),
        (True, "Ja"),
        (False, "Nein")
    )
    terms_of_payment = models.CharField(choices=terms_of_payment_choices, blank=True, null=True, max_length=200,
                                        verbose_name="Zahlungsbedingung")
    terms_of_delivery = models.CharField(choices=terms_of_delivery_choices, blank=True, null=True, max_length=200,
                                         verbose_name="Lieferkonditionen")
    delivery_address = models.ForeignKey(Adress, null=True, blank=True, verbose_name="Lieferadresse")
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    pickable = models.NullBooleanField(choices=CHOICES, verbose_name="Pickbereit")

    def __init__(self, *args, **kwargs):
        super(Mission, self).__init__(*args, **kwargs)
        self.__original_pickable = self.pickable

    def save(self, *args, **kwargs):
        # if self.__original_pickable != self.pickable:
        #     if self.pickable is True:
        #             self.status = "PICKBEREIT"
        #     elif self.pickable is False:
        #         self.status = "AUSSTEHEND"

        if self.mission_number == "":
            today = date.today().strftime('%d%m%y')
            count = Mission.objects.filter(mission_number__icontains=today).count()+1
            self.mission_number = f"A{today}-{count}"

        if self.billing_number == "":
            all_missions = Mission.objects.all()
            max_billing_number = all_missions.aggregate(Max('billing_number')).get("billing_number__max")
            # Da billing_number ein Charfield ist wird es nicht die höchste Nummer packen, ist aber hier egal
            if all_missions.count() >= 1 and max_billing_number != "":
                if max_billing_number[0].isalpha():
                    max_billing_number = max_billing_number[1:]
                self.billing_number = f"R{int(max_billing_number) + 1}"
            else:
                self.billing_number = "R135454321"

        super().save(force_insert=False, force_update=False, *args, **kwargs)

    def __str__(self):
        return self.mission_number

    def get_absolute_url(self):
        return reverse("mission:detail", kwargs={"pk": self.id})


class ProductMission(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Artikel")
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, unique=False, blank=False, null=False,
                                verbose_name="Auftrag")
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

    # def save(self, *args, **kwargs):
    #     print(f"safe rein: {self.confirmed}")
    #     product_missions = self.mission.productmission_set.all()
    #     all_scanned = True
    #     has_confirmed_false = False
    #     if self.confirmed == "0":
    #         has_confirmed_false = True
    #
    #     if self.confirmed == "1" or self.confirmed == "0":
    #         self.mission.status = "WARENAUSGANG"
    #     else:
    #         all_scanned = False
    #
    #     for product_mission in product_missions:
    #         if self.id != product_mission.id:
    #             if product_mission.confirmed is True or product_mission.confirmed is False:
    #                 self.mission.status = "WARENAUSGANG"
    #                 if product_mission.confirmed is False:
    #                     has_confirmed_false = True
    #             else:
    #                 all_scanned = False
    #     if all_scanned is True and product_missions.exists():
    #         self.mission.status = "LIEFERUNG"
    #         if has_confirmed_false is True:
    #             self.mission.status = "TEILLIEFERUNG"
    #
    #     self.mission.save()
    #     super().save(*args, **kwargs)