from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError


class Stock(models.Model):
    IGNORE_CHOICES = (
        ('IGNORE', 'Ja'),
        ('NOT_IGNORE', 'Nein'),
    )

    ean_vollstaendig = models.CharField(max_length=250)
    bestand = models.IntegerField(null=True, blank=True)
    ean_upc = models.CharField(max_length=250, null=True, blank=True)
    lagerplatz = models.CharField(max_length=250, null=True, blank=True)
    regal = models.CharField(max_length=250, null=True, blank=True)
    zustand = models.CharField(max_length=250, null=True, blank=True)
    scanner = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=250, null=True, blank=True)
    karton = models.CharField(max_length=250, null=True, blank=True)
    box = models.CharField(max_length=250, null=True, blank=True)
    aufnahme_datum = models.CharField(max_length=250, null=True, blank=True)
    ignore_unique = models.CharField(max_length=250, null=True, blank=True, choices=IGNORE_CHOICES,
                                     verbose_name="Block")

    def get_absolute_url(self):
        return reverse("stock:list")

    def __str__(self):
        return str(self.ean_vollstaendig)

    def clean(self):
        if self.ignore_unique == "IGNORE":
            return

        stocks = Stock.objects.filter(ean_vollstaendig=self.ean_vollstaendig, zustand=self.zustand,
                                      lagerplatz=self.lagerplatz)
        if stocks.count() > 0:
            raise ValidationError(_('Lagerbestand schon vorhanden'))


class Stockdocument(models.Model):
    document = models.FileField(upload_to='documents/', null=True, blank=False)
    uploaded_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse("stock:documentdetail", kwargs={"pk": self.id})
