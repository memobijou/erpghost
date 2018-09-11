from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.


class Channel(models.Model):
    name = models.CharField(null=True, blank=True, max_length=200, verbose_name="Channel")
    api_data = models.ForeignKey("client.ApiData", null=True, blank=True)


class RefillOrder(models.Model):
    refill_order_id = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nachfüllauftrags ID")
    user = models.ForeignKey(get_user_model(), on_delete=models.deletion.SET_NULL, null=True, blank=True)
    completed = models.NullBooleanField(null=True, blank=True, verbose_name="Erledigt")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save()
        if self.refill_order_id is None or self.refill_order_id == "":
            self.refill_order_id = f"NA{self.pk}"
        super().save()


class RefillOrderOutbookStock(models.Model):
    refill_order = models.ForeignKey(RefillOrder, null=True, blank=True, on_delete=models.deletion.SET_NULL)
    product_mission = models.ForeignKey("mission.ProductMission", null=True, blank=True)
    amount = models.IntegerField(verbose_name="Menge", null=True, blank=True)
    position = models.CharField(verbose_name="Lagerplatz", null=True, blank=True, max_length=200)
    booked_out = models.NullBooleanField(verbose_name="Ausgebucht", blank=True, null=True)
    booked_out_amount = models.IntegerField(verbose_name="Ausgebuchte Menge", null=True, blank=True)
    stock = models.ForeignKey("stock.Stock", null=True, blank=True, verbose_name="Bestand")
