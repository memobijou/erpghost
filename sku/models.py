from django.db import models


class Sku(models.Model):
    sku = models.CharField(max_length=200, null=True, blank=True, verbose_name="SKU")
    state = models.CharField(blank=True, null=True, max_length=200, verbose_name="Zustand")
    purchasing_price = models.FloatField(null=True, blank=True, verbose_name="Einkaufspreis")

    product = models.ForeignKey("product.Product", null=True, blank=True)

    def __str__(self):
        return str(self.sku)
