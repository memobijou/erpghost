from django.db import models
import datetime
from django.utils import timezone
from django.core.urlresolvers import reverse

# Create your models here.

class Stock(models.Model):
    ean_vollstaendig = models.CharField(max_length=250)
    bestand = models.IntegerField(null=True, blank=True)
    ean_upc =  models.CharField(max_length=250, null=True, blank=True)
    lagerplatz = models.CharField(max_length=250, null=True, blank=True)
    zustand = models.CharField(max_length=250, null=True, blank=True)
    scanner = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=250, null=True, blank=True)
    karton = models.CharField(max_length=250, null=True, blank=True)
    box = models.IntegerField(null=True, blank=True)
    bereich = models.CharField(max_length=250, null=True, blank=True)
    ueberpruefung = models.CharField(max_length=250, null=True, blank=True)
    aufnahme_datum = models.CharField(max_length=250, null=True, blank=True)

    def get_absolute_url(self):
        return reverse("stock:list")

    def __str__(self):
        return str(self.ean_vollstaendig)

class Stockdocument(models.Model):
    document = models.FileField(upload_to='documents/', null=True, blank=False)
    uploaded_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse("stock:documentdetail", kwargs={"pk": self.id})