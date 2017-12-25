from django.db import models

# Create your models here.

class Warehouse(models.Model):
	gesamt_kubik = models.FloatField(null=False, blank=True, default=None)
	ist_kubik = models.FloatField(null=False, blank=True, default=None)
	diff_kubik = models.FloatField(null=False, blank=True, default=None)
	position = models.CharField(blank=True, null=False, max_length=13)

	def __str__(self):
		return self.position