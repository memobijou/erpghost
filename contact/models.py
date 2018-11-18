from django.db import models
from adress.models import Adress


class Bank(models.Model):
    bank = models.CharField(blank=True, null=True, max_length=200, verbose_name="Bank")
    bic = models.CharField(blank=True, null=True, max_length=200, verbose_name="BIC")
    iban = models.CharField(blank=True, null=True, max_length=200, verbose_name="IBAN")


class Contact(models.Model):
    first_name_last_name = models.CharField(blank=True, null=True, max_length=200, verbose_name="Name")
    telefon = models.CharField(blank=True, null=True, max_length=200, verbose_name="Telefon")
    fax = models.CharField(blank=True, null=True, max_length=200, verbose_name="Fax")
    email = models.CharField(blank=True, null=True, max_length=200, verbose_name="Email")
    website = models.CharField(blank=True, null=True, max_length=200, verbose_name="Webseite")
    website_conditions_link = models.CharField(blank=True, null=True, max_length=200, verbose_name="Webseite")
    skype_id = models.CharField(blank=True, null=True, max_length=200)
    billing_address = models.ForeignKey(Adress, null=True, blank=True, related_name='billing_contact',
                                        on_delete=models.deletion.SET_NULL)
    delivery_address = models.ForeignKey(Adress, null=True, blank=True, related_name='delivery_contact',
                                         on_delete=models.deletion.SET_NULL)
    company_image = models.ImageField(verbose_name="Firmenlogo", blank=True, null=True)
    bank = models.ManyToManyField(Bank)
    commercial_register = models.CharField(blank=True, null=True, max_length=200, verbose_name="Handelsregister")
    tax_number = models.CharField(blank=True, null=True, max_length=200, verbose_name="Steuernummer")
    sales_tax_identification_number = models.CharField(blank=True, null=True, max_length=200, verbose_name="Ust-IdNr.")
    billing_addresses = models.ManyToManyField(Adress, verbose_name="Zusätzliche Rechnungsadressen",
                                               related_name='billing_contact_many')
    delivery_addresses = models.ManyToManyField(Adress, verbose_name="Zusätzliche Lieferadressen",
                                                related_name="delivery_contact_many")
