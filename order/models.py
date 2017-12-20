from django.db import models
import datetime
from django.utils import timezone
from django.core.urlresolvers import reverse

# Create your models here.

class Order(models.Model):
	ordernumber = models.CharField(max_length=13)
	delivery_date = models.DateField(default=datetime.date.today)
	status = models.CharField(max_length=25, null=True, blank=True)

	#delivery_date = models.DateTimeField(default=timezone.now)

	def __str__(self):
		return self.ordernumber

	def get_absolute_url(self):
		return reverse("order:detail", kwargs={"pk": self.id})