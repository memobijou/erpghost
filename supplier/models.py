from django.db import models
from contact.models import Contact
from django.core.urlresolvers import reverse


# Create your models here.
class Supplier(models.Model):
    contact = models.ForeignKey(Contact, null=True, blank=True, related_name='supplier', verbose_name="Kontaktdaten")
    supplier_number = models.CharField(max_length=200, verbose_name="Lieferantennummer", null=True, blank=True)
    # contact = models.OneToOneField(Contact,blank=True,null=True,related_name="supplier")

    def __str__(self):
        return f"{self.contact.billing_address.firma}"

    def get_absolute_url(self):
        return reverse("supplier:detail", kwargs={"pk": self.id})
