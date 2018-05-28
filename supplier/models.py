from django.db import models
from contact.models import Contact
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.db.models.functions import Cast


# Create your models here.
class Supplier(models.Model):
    contact = models.ForeignKey(Contact, null=True, blank=True, related_name='supplier', verbose_name="Kontaktdaten")
    supplier_number = models.CharField(max_length=200, verbose_name="Lieferantennummer", null=True, blank=True)
    # contact = models.OneToOneField(Contact,blank=True,null=True,related_name="supplier")

    def __str__(self):
        return f"{self.contact.billing_address.firma}"

    def get_absolute_url(self):
        return reverse("supplier:detail", kwargs={"pk": self.id})

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.supplier_number is None or self.supplier_number == "":
            self.supplier_number = f"LF{self.pk+1}"
        super().save()
