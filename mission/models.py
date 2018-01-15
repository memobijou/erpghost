from django.db import models
import datetime
from django.core.urlresolvers import reverse
from product.models import Product


# Create your models here.
class Mission(models.Model):
    mission_number = models.CharField(max_length=13)
    delivery_date = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=25, null=True, blank=True)
    products = models.ManyToManyField(Product, through="ProductMission")

    def __str__(self):
        return self.mission_number

    def get_absolute_url(self):
        return reverse("mission:detail", kwargs={"pk": self.id})

class ProductMission(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, unique=False, blank=False, null=False)
    amount = models.IntegerField(null=False, blank=False, default=0)

    confirmed = models.NullBooleanField()

    def __str__(self):
    	return str(self.product) + " : " + str(self.order) + " : " + str(self.amount)
