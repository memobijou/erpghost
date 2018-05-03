from django.db import models
from contact.models import Contact


# Create your models here.
class Client(models.Model):
    name = models.CharField(blank=True, null=False, max_length=200)
    contact = models.OneToOneField(Contact, blank=True, null=True, related_name="client")
    qr_code = models.ImageField(verbose_name="QR-Code", blank=True, null=True)

    def __str__(self):
        return f"{self.contact.billing_address.firma} - {self.contact.billing_address.strasse} - " \
               f"{self.contact.billing_address.hausnummer} - {self.contact.billing_address.zip} - " \
               f"{self.contact.billing_address.place}"
