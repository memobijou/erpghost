from django.db import models
from contact.models import Contact
from django.core.urlresolvers import reverse

# Create your models here.


class Customer(models.Model):
    customer_number = models.CharField(max_length=200, verbose_name="Kunden-Nr.", null=True, blank=True)
    contact = models.ForeignKey(Contact, null=True, blank=True, related_name='customer', verbose_name="Kontaktdaten")

    def __str__(self):
        return f"{self.contact.billing_address.firma}"

    def get_absolute_url(self):
        return reverse("customer:detail", kwargs={"pk": self.id})
