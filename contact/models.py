from django.db import models
from adress.models import Adress


class Bank(models.Model):
    bank = models.CharField(blank=True, null=True, max_length=200, verbose_name="Bank")
    bic = models.CharField(blank=True, null=True, max_length=200, verbose_name="BIC")
    iban = models.CharField(blank=True, null=True, max_length=200, verbose_name="IBAN")


class Contact(models.Model):
    telefon = models.CharField(blank=True, null=True, max_length=200, verbose_name="Telefon")
    fax = models.CharField(blank=True, null=True, max_length=200, verbose_name="Fax")
    email = models.CharField(blank=True, null=True, max_length=200, verbose_name="Email")
    website = models.CharField(blank=True, null=True, max_length=200, verbose_name="Webseite")
    skype_id = models.CharField(blank=True, null=True, max_length=200)
    adress = models.ForeignKey(Adress, null=True, blank=True, related_name='contact')
    company_image = models.ImageField(verbose_name="Firmenlogo", blank=True, null=True)
    bank = models.ManyToManyField(Bank)
    commercial_register = models.CharField(blank=True, null=True, max_length=200, verbose_name="Handelsregister")
    tax_number = models.CharField(blank=True, null=True, max_length=200, verbose_name="Steuernummer")
    sales_tax_identification_number = models.CharField(blank=True, null=True, max_length=200, verbose_name="Ust-IdNr.")
