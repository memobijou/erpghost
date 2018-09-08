from django.db import models
from contact.models import Contact
from django.core.urlresolvers import reverse
from django.db.models import Max
# Create your models here.


class Customer(models.Model):
    customer_number = models.CharField(max_length=200, verbose_name="Kunden-Nr.", null=True, blank=True)
    contact = models.ForeignKey(Contact, null=True, blank=True, related_name='customer', verbose_name="Kontaktdaten")

    def __str__(self):
        if self.contact.billing_address is not None and self.contact.billing_address.firma is not None:
            return f"{self.contact.billing_address.firma}"
        else:
            return self.contact.first_name_last_name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        if self.customer_number is None or self.customer_number == "":
            self.customer_number = f"KD{self.pk+1}"
        super().save()

    def get_absolute_url(self):
        return reverse("customer:detail", kwargs={"pk": self.id})
