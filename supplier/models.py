from django.db import models
from contact.models import Contact


# Create your models here.
# Create your models here.
class Supplier(models.Model):
    name = models.CharField(blank=True, null=False, max_length=13)
    contact = models.ForeignKey(Contact, null=True, blank=True, related_name='supplier')

    # contact = models.OneToOneField(Contact,blank=True,null=True,related_name="supplier")

    def __str__(self):
        return self.name + "----------" + str(self.contact)
