from django.db import models


# Create your models here.
class Adress(models.Model):
    firma = models.CharField(blank=True, null=False, max_length=13)
    anrede = models.CharField(blank=True, null=False, max_length=13)
    title = models.CharField(blank=True, null=False, max_length=13)
    vorname = models.CharField(blank=True, null=False, max_length=13)
    nachname = models.CharField(blank=True, null=False, max_length=13)
    strasse = models.CharField(blank=True, null=False, max_length=13)
    hausnummer = models.CharField(blank=True, null=False, max_length=13)
    adresszusatz = models.CharField(blank=True, null=False, max_length=13)
    adresszusatz2 = models.CharField(blank=True, null=False, max_length=13)

    def __str__(self):
        return str(self.firma) + str(self.contact)
