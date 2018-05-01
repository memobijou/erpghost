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

    def save(self, *args, **kwargs):
        if self.supplier_number == "" or self.supplier_number is None:
            all_suppliers = Supplier.objects.all()
            max_supplier_number = all_suppliers.aggregate(Max('supplier_number')).get("supplier_number__max")
            # Da supplier_number ein Charfield ist wird es nicht die höchste Nummer packen, ist aber hier egal
            if all_suppliers.count() >= 1 and max_supplier_number != "":
                if max_supplier_number[0].isalpha():
                    max_supplier_number = max_supplier_number[1:]
                self.supplier_number = f"L{int(max_supplier_number) + 1}"
            else:
                self.supplier_number = "L383954521"
        super().save(force_insert=False, force_update=False, *args, **kwargs)