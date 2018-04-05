from django.db import models
from supplier.models import Supplier


class Manufacturer(models.Model):
    name = models.CharField(blank=True, null=False, max_length=200, verbose_name="Hersteller")


class Brand(models.Model):
    name = models.CharField(blank=True, null=False, max_length=200, verbose_name="Markenname")


class Product(models.Model):
    main_image = models.ImageField(verbose_name="Bild", null=True, blank=True)

    ean = models.CharField(blank=True, null=False, max_length=200, verbose_name="EAN")
    manufacturer = models.CharField(max_length=500, null=True, blank=True, default="", verbose_name="Hersteller")
    brandname = models.CharField(max_length=500, null=True, blank=True, default="", verbose_name="Markenname")
    part_number = models.CharField(blank=True, null=True, max_length=200, verbose_name="Herstellernummer")

    title = models.CharField(max_length=500, null=True, blank=True, default="", verbose_name="Titel")
    short_description = models.TextField(null=True, blank=True, default="", verbose_name="Kurzbeschreibung")
    description = models.TextField(null=True, blank=True, default="", verbose_name="Beschreibung")

    height = models.FloatField(null=True, blank=True, default=None, verbose_name="Höhe")
    width = models.FloatField(null=True, blank=True, default=None, verbose_name="Breite")
    length = models.FloatField(null=True, blank=True, default=None, verbose_name="Länge")

    def __str__(self):
        return f"{self.ean}"

    @property
    def calc_volume(self):
        if self.height and self.width and self.length:
            return self.height * self.width * self.length
