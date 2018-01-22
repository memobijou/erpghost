from django.db import models
from product.models import Product


class Masterdata(models.Model):
    height = models.FloatField(null=True, blank=True, default=None)
    width = models.FloatField(null=True, blank=True, default=None)
    length = models.FloatField(null=True, blank=True, default=None)

    product = models.OneToOneField(Product, blank=True, null=True, related_name="masterdata")

    def __str__(self):
        return (str(self.height))

    @property
    def calc_volume(self):
        return self.height * self.width * self.length
