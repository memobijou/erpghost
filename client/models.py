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

    def get_billing_address_as_html(self):
        billing_address = ""
        if self.contact is not None and self.contact.billing_address is not None:
            if self.contact.billing_address.firma is not None:
                billing_address += f"{self.contact.billing_address.firma}<br/>"
            if self.contact.billing_address.strasse is not None:
                billing_address += f"{self.contact.billing_address.strasse}"
            if self.contact.billing_address.hausnummer is not None:
                billing_address += f" {self.contact.billing_address.hausnummer}<br/>"
            else:
                billing_address += f"<br/>"
            if self.contact.billing_address.zip is not None:
                billing_address += f"{self.contact.billing_address.zip}"
            if self.contact.billing_address.place is not None:
                billing_address += f" {self.contact.billing_address.place}<br/>"
            else:
                billing_address += "<br/>"
            return billing_address

    def get_delivery_address_as_html(self):
        delivery_address = ""
        if self.contact is not None and self.contact.delivery_address is not None:
            if self.contact.delivery_address.firma is not None:
                delivery_address += f"{self.contact.delivery_address.firma}<br/>"
            if self.contact.delivery_address.strasse is not None:
                delivery_address += f"{self.contact.delivery_address.strasse}"
            if self.contact.delivery_address.hausnummer is not None:
                delivery_address += f" {self.contact.delivery_address.hausnummer}<br/>"
            else:
                delivery_address += f"<br/>"
            if self.contact.delivery_address.zip is not None:
                delivery_address += f"{self.contact.delivery_address.zip}"
            if self.contact.delivery_address.place is not None:
                delivery_address += f" {self.contact.delivery_address.place}<br/>"
            else:
                delivery_address += "<br/>"
            return delivery_address


class ApiData(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Bezeichnung")
    client = models.ForeignKey("client.Client", null=True, blank=True, verbose_name="Mandant",
                               on_delete=models.SET_NULL)
    # amazon
    account_id_encrypted = models.CharField(max_length=400, null=True, blank=True, verbose_name="Account ID")
    access_key_encrypted = models.CharField(max_length=400, null=True, blank=True, verbose_name="Access Key")
    secret_key_encrypted = models.CharField(max_length=400, null=True, blank=True, verbose_name="Secret Key")
    # ebay
    app_client_id = models.CharField(max_length=400, null=True, blank=True, verbose_name="Client ID")
    client_secret = models.CharField(max_length=400, null=True, blank=True, verbose_name="Client Secret")
    authentication_token = models.CharField(max_length=400, null=True, blank=True,
                                            verbose_name="Authentifizierungstoken")
    access_token = models.CharField(max_length=4000, null=True, blank=True, verbose_name="Zugriffstoken")
    refresh_token = models.CharField(max_length=4000, null=True, blank=True, verbose_name="Aktualisierungstoken")
