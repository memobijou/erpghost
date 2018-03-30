from django.db import models
from contact.models import Contact
from django.core.urlresolvers import reverse

# Create your models here.


class Customer(models.Model):
    name = models.CharField(blank=True, null=False, max_length=13)
    contact = models.ForeignKey(Contact, null=True, blank=True, related_name='customer', verbose_name="Kontaktdaten")

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse("customer:detail", kwargs={"pk": self.id})
