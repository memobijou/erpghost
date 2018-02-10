from django.db import models
import datetime
from django.core.urlresolvers import reverse
from product.models import Product
from datetime import date


# Create your models here.
class Mission(models.Model):
    mission_number = models.CharField(max_length=13, blank=True)
    delivery_date = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=25, null=True, blank=True, default="OFFEN")
    products = models.ManyToManyField(Product, through="ProductMission")
    CHOICES = (
        (None, "----"),
        (True, "Ja"),
        (False, "Nein")
    )
    verified = models.NullBooleanField(choices=CHOICES)
    pickable = models.NullBooleanField(choices=CHOICES)

    def __init__(self, *args, **kwargs):
        super(Mission, self).__init__(*args, **kwargs)
        self.__original_verified = self.verified
        self.__original_pickable = self.pickable

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.__original_verified != self.verified:
            if self.verified is True:
                # name changed - do something here
                self.status = "AKZEPTIERT"
            elif self.verified is False:
                self.status = "ABGELEHNT"
        if self.verified is True:
            if self.__original_pickable != self.pickable:
                if self.pickable is True:
                    self.status = "PICKBEREIT"
                elif self.pickable is False:
                    self.status = "AUSSTEHEND"
                else:
                    if self.verified is True:
                        # name changed - do something here
                        self.status = "AKZEPTIERT"
                    elif self.verified is False:
                        self.status = "ABGELEHNT"

        if self.mission_number == "":
            today = date.today().strftime('%d%m%y')
            count = Mission.objects.filter(mission_number__icontains=today).count()+1
            self.mission_number = f"A{today}-{count}"
        super().save(force_insert=False, force_update=False, *args, **kwargs)

    def __str__(self):
        return self.mission_number

    def get_absolute_url(self):
        return reverse("mission:detail", kwargs={"pk": self.id})


class ProductMission(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, unique=False, blank=False, null=False)
    amount = models.IntegerField(null=False, blank=False, default=0)
    missing_amount = models.IntegerField(null=True, blank=True)

    confirmed = models.NullBooleanField()

    def __str__(self):
        return str(self.product) + " : " + str(self.mission) + " : " + str(self.amount)

    @property
    def real_amount(self):
        if self.amount and self.missing_amount:
            return self.amount - self.missing_amount
        else:
            return self.amount
