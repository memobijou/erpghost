from django.db import models
from contact.models import Contact
from django.core.urlresolvers import reverse
from django.db.models import Max
# Create your models here.


class Customer(models.Model):
    customer_number = models.CharField(max_length=200, verbose_name="Kunden-Nr.", null=True, blank=True)
    contact = models.ForeignKey(Contact, null=True, blank=True, related_name='customer', verbose_name="Kontaktdaten")

    def __str__(self):
        return f"{self.contact.billing_address.firma}"

    def save(self, *args, **kwargs):
        if self.customer_number == "" or self.customer_number is None:
            all_customers = Customer.objects.all()
            max_customer_number = all_customers.aggregate(Max('customer_number')).get("customer_number__max")
            # Da customer_number ein Charfield ist wird es nicht die höchste Nummer packen, ist aber hier egal

            if all_customers.count() >= 1 and max_customer_number != "":
                if max_customer_number[0].isalpha():
                    max_customer_number = max_customer_number[1:]
                self.customer_number = f"KD{int(max_customer_number) + 1}"
            else:
                self.customer_number = "KD533454723"
        super().save(force_insert=False, force_update=False, *args, **kwargs)

    def get_absolute_url(self):
        return reverse("customer:detail", kwargs={"pk": self.id})
