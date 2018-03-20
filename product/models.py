from django.db import models
from supplier.models import Supplier


class Manufacturer(models.Model):
    name = models.CharField(blank=True, null=False, max_length=200, verbose_name="Hersteller")


class Product(models.Model):
    ean = models.CharField(blank=True, null=False, max_length=13, verbose_name="EAN")
    manufacturer = models.ForeignKey(Manufacturer, null=True, related_name="manufacturer", verbose_name="Hersteller")
    part_number = models.CharField(blank=True, null=True, max_length=200, verbose_name="Herstellernummer")

    def __str__(self):
        return self.ean

