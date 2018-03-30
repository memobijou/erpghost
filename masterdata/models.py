from django.db import models
from product.models import Product


class Masterdata(models.Model):
    title = models.CharField(max_length=500, null=True, blank=True, default="", verbose_name="Titel")
    short_description = models.TextField(null=True, blank=True, default="", verbose_name="Kurzbeschreibung")
    description = models.TextField(null=True, blank=True, default="", verbose_name="Beschreibung")

    height = models.FloatField(null=True, blank=True, default=None)
    width = models.FloatField(null=True, blank=True, default=None)
    length = models.FloatField(null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.title}"

    @property
    def calc_volume(self):
        return self.height * self.width * self.length
