from django.db import models
from contact.models import Contact


# Create your models here.
class Client(models.Model):
    name = models.CharField(blank=True, null=False, max_length=13)
    contact = models.OneToOneField(Contact, blank=True, null=True, related_name="client")

    def __str__(self):
        return f"{self.name} - {self.contact.adress.firma} - {self.contact.adress.strasse} - " \
               f"{self.contact.adress.hausnummer} - {self.contact.adress.zip} - {self.contact.adress.place}"
