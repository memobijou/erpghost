from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.


class Channel(models.Model):
    name = models.CharField(null=True, blank=True, max_length=200, verbose_name="Bezeichnung")
    market = models.CharField(null=True, blank=True, max_length=200, verbose_name="Marktplatz")
    api_data = models.ForeignKey("client.ApiData", null=True, blank=True)
    client = models.ForeignKey("client.Client", null=True, blank=True, verbose_name="Mandant",
                               on_delete=models.SET_NULL)

    def __str__(self):
        return f'{self.market or ""} - {self.name or ""}'


class OfferManager(models.Manager):
    def bulk_create(self, objs, batch_size=None):
        from sku.models import Sku  # cyclic import error
        for obj in objs:
            sku_instance = Sku.objects.filter(sku=self.sku).first()
            if sku_instance is not None:
                obj.sku_instance = sku_instance
        super().bulk_create(objs)


class Offer(models.Model):
    objects = OfferManager()

    sku = models.CharField(null=True, blank=True, max_length=200, verbose_name="Angebot")
    asin = models.CharField(null=True, blank=True, max_length=200, verbose_name="Angebot")
    amount = models.IntegerField(verbose_name="Menge", null=True, blank=True, default="0")
    sku_instance = models.OneToOneField("sku.Sku", null=True, blank=True)

    def __init__(self, *args, **kwargs):
        from sku.models import Sku
        self.sku_class = Sku
        super().__init__(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        sku_instance = self.sku_class.objects.filter(sku=self.sku).first()  # cyclic import error
        if sku_instance is not None:
            self.sku_instance = sku_instance
        super().save()


class RefillOrder(models.Model):
    refill_order_id = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nachfüllauftrags ID")
    user = models.ForeignKey(get_user_model(), on_delete=models.deletion.SET_NULL, null=True, blank=True)
    booked_out = models.NullBooleanField(null=True, blank=True, verbose_name="Ausgebucht")
    booked_in = models.NullBooleanField(null=True, blank=True, verbose_name="Eingebucht")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save()
        if self.refill_order_id is None or self.refill_order_id == "":
            self.refill_order_id = f"NA{self.pk}"
        super().save()


class RefillOrderOutbookStock(models.Model):
    refill_order = models.ForeignKey(RefillOrder, null=True, blank=True, on_delete=models.deletion.SET_NULL)
    product_mission = models.ForeignKey("mission.ProductMission", null=True, blank=True,
                                        on_delete=models.deletion.SET_NULL)
    amount = models.IntegerField(verbose_name="Menge", null=True, blank=True)
    position = models.CharField(verbose_name="Lagerplatz", null=True, blank=True, max_length=200)
    booked_out = models.NullBooleanField(verbose_name="Ausgebucht", blank=True, null=True)
    booked_out_amount = models.IntegerField(verbose_name="Ausgebuchte Menge", null=True, blank=True)
    stock = models.ForeignKey("stock.Stock", null=True, blank=True, verbose_name="Bestand",
                              on_delete=models.deletion.SET_NULL)


class RefillOrderInbookStock(models.Model):
    refill_order = models.ForeignKey(RefillOrder, null=True, blank=True, on_delete=models.deletion.SET_NULL)
    product = models.ForeignKey("product.Product", null=True, blank=True, on_delete=models.deletion.SET_NULL)
    state = models.CharField(verbose_name="Zustand", null=True, blank=True, max_length=200)
    amount = models.IntegerField(verbose_name="Menge", null=True, blank=True)
    position = models.CharField(verbose_name="Lagerplatz", null=True, blank=True, max_length=200)
    booked_in = models.NullBooleanField(verbose_name="Ausgebucht", blank=True, null=True)
    booked_in_amount = models.IntegerField(verbose_name="Ausgebuchte Menge", null=True, blank=True)
    stock = models.ForeignKey("stock.Stock", null=True, blank=True, verbose_name="Bestand",
                              on_delete=models.deletion.SET_NULL)
