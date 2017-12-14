from django.db import models

# Create your models here.

class Order(models.Model):
	ordernumber = models.CharField(max_length=13)

	def __str__(self):
		return self.ordernumber