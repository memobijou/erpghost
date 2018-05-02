from django.db import models


# Create your models here.
class Adress(models.Model):
    firma = models.CharField(blank=True, null=True, max_length=200, verbose_name="Firma")
    anrede = models.CharField(blank=False, null=True, max_length=200, verbose_name="Anrede")
    title = models.CharField(blank=False, null=True, max_length=13, verbose_name="Titel")
    vorname = models.CharField(blank=False, null=True, max_length=200, verbose_name="Vorname")
    nachname = models.CharField(blank=False, null=True, max_length=200, verbose_name="Nachname")
    strasse = models.CharField(blank=False, null=True, max_length=200, verbose_name="Straße")
    hausnummer = models.CharField(blank=False, null=True, max_length=200, verbose_name="Hausnummer")
    adresszusatz = models.CharField(blank=True, null=True, max_length=200, verbose_name="Adresszusatz")
    adresszusatz2 = models.CharField(blank=True, null=True, max_length=200, verbose_name="Adresszusatz 2")
    zip = models.CharField(blank=False, null=True, max_length=200, verbose_name="Plz")
    place = models.CharField(blank=False, null=True, max_length=200, verbose_name="Ort")

    def __str__(self):
        return f"{self.firma} - {self.strasse} {self.hausnummer} - {self.zip} {self.place}"
