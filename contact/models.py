from django.db import models
from adress.models import Adress

class Contact(models.Model):
	telefon= models.CharField(blank=True, null=False, max_length=13)
	email = models.CharField(blank=True, null=False, max_length=13)
	skype_id = models.CharField(blank=True, null=False, max_length=13)
	adress = models.ForeignKey(Adress, null=True, blank=True,related_name = 'contact')
	
	def __str__(self):
		return self.telefon + self.email + self.skype_id

