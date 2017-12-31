from django.db import models
from product.models import Product

class Sku(models.Model):
	sku= models.IntegerField(null=True, blank=True, default=None)
	zustand = models.CharField(blank=True, null=False, max_length=13)
	nettopreis= models.FloatField(null=True, blank=True, default=None)
	bruttopreis= models.FloatField(null=True, blank=True, default=None)
	menge= models.IntegerField(null=True, blank=True, default=None)
	
	product = models.OneToOneField(Product,blank=True,null=True,related_name="sku")

	def __str__(self):
		return (str(self.sku)) 