from django.db import models
from position.models import Position


class Product(models.Model):
    ean = models.CharField(blank=True, null=False, max_length=13)
    positions = models.ManyToManyField(Position, through="PositionProduct")

    def __str__(self):
        return self.ean


class PositionProduct(models.Model):
    products = models.ForeignKey(Product, on_delete=models.CASCADE)
    positions = models.ForeignKey(Position, on_delete=models.CASCADE, unique=False, blank=False, null=False)

    def __str__(self):
        return str(self.positions) + " : " + str(self.products)
