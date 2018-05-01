from django.db import models


# Create your models here.
class Adress(models.Model):
    firma = models.CharField(blank=True, null=True, max_length=200)
    anrede = models.CharField(blank=False, null=True, max_length=200)
    title = models.CharField(blank=False, null=True, max_length=13)
    vorname = models.CharField(blank=False, null=True, max_length=200)
    nachname = models.CharField(blank=False, null=True, max_length=200)
    strasse = models.CharField(blank=False, null=True, max_length=200)
    hausnummer = models.CharField(blank=False, null=True, max_length=200)
    adresszusatz = models.CharField(blank=True, null=True, max_length=200)
    adresszusatz2 = models.CharField(blank=True, null=True, max_length=200)
    zip = models.CharField(blank=False, null=True, max_length=200)
    place = models.CharField(blank=False, null=True, max_length=200)

    def __str__(self):
        return f"{self.firma} - {self.strasse} {self.hausnummer} - {self.zip} {self.place}"
