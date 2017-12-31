from django.db import models
from contact.models import Contact
# Create your models here.
class Client(models.Model):
	name  = models.CharField(blank=True, null=False, max_length=13)
	contact = models.OneToOneField(Contact,blank=True,null=True,related_name="client")

	def __str__(self):
		return self.name

