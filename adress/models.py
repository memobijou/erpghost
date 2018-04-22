from django.db import models


# Create your models here.
class Adress(models.Model):
    firma = models.CharField(blank=True, null=False, max_length=200)
    anrede = models.CharField(blank=True, null=False, max_length=200)
    title = models.CharField(blank=True, null=False, max_length=13)
    vorname = models.CharField(blank=True, null=False, max_length=200)
    nachname = models.CharField(blank=True, null=False, max_length=200)
    strasse = models.CharField(blank=True, null=False, max_length=200)
    hausnummer = models.CharField(blank=True, null=False, max_length=200)
    adresszusatz = models.CharField(blank=True, null=False, max_length=200)
    adresszusatz2 = models.CharField(blank=True, null=False, max_length=200)
    zip = models.CharField(blank=True, null=False, max_length=200)
    place = models.CharField(blank=True, null=False, max_length=200)

    def __str__(self):
        return str(self.firma) + str(self.contact)
