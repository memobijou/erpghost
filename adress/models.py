from django.db import models


# Create your models here.
class Adress(models.Model):
    firma = models.CharField(blank=True, null=True, max_length=200, verbose_name="Firma")
    anrede = models.CharField(blank=False, null=True, max_length=200, verbose_name="Anrede")
    title = models.CharField(blank=False, null=True, max_length=13, verbose_name="Titel")
    vorname = models.CharField(blank=False, null=True, max_length=200, verbose_name="Vorname")
    nachname = models.CharField(blank=False, null=True, max_length=200, verbose_name="Nachname")
    first_name_last_name = models.CharField(blank=True, null=True, max_length=200, verbose_name="Name")
    strasse = models.CharField(blank=False, null=True, max_length=200, verbose_name="Straße")
    street_and_housenumber = models.CharField(blank=True, null=True, max_length=200,
                                              verbose_name="Straße und Hasunummer")
    address_line_1 = models.CharField(blank=True, null=True, max_length=200, verbose_name="Adresslinie 1")
    address_line_2 = models.CharField(blank=True, null=True, max_length=200, verbose_name="Adresslinie 2")
    address_line_3 = models.CharField(blank=True, null=True, max_length=200, verbose_name="Adresslinie 3")
    hausnummer = models.CharField(blank=False, null=True, max_length=200, verbose_name="Hausnummer")
    adresszusatz = models.CharField(blank=True, null=True, max_length=200, verbose_name="Adresszusatz")
    adresszusatz2 = models.CharField(blank=True, null=True, max_length=200, verbose_name="Adresszusatz 2")
    zip = models.CharField(blank=False, null=True, max_length=200, verbose_name="Plz")
    place = models.CharField(blank=False, null=True, max_length=200, verbose_name="Ort")
    country_code = models.CharField(blank=True, null=True, max_length=200, verbose_name="Ländercode")
    country = models.CharField(blank=True, null=True, max_length=200, verbose_name="Land")

    def __str__(self):
        return f"{self.firma} - {self.strasse} {self.hausnummer} - {self.zip} {self.place}"
