from django.db import models
from django.core.urlresolvers import reverse
# from columns.models import ColumnPosition
# from product.models import Product
from column.models import Column


# Create your models here.

class Position(models.Model):
    shelf = models.CharField(blank=True, null=False, max_length=13)
    level = models.CharField(blank=True, null=False, max_length=13)
    place = models.CharField(blank=True, null=False, max_length=13)
    halle = models.CharField(blank=True, null=False, max_length=13)
    column = models.ForeignKey(Column, null=True, blank=True)

    def __str__(self):
        return str(self.halle) + "-" + str(self.place) + "-" + str(self.level) + "-" + str(self.shelf)

    @property
    def reserved_volume(self):
        total = 0
        for p in self.positionproductorder_set.all():
            total = total + p.productorder.product.masterdata.calc_volume
        return total

    @property
    def available_volume(self):
        total = self.reserved_volume - self.max_volume

        return total * -1

    @property
    def max_volume(self):
        vol = 0
        if self.column:
            positions = self.column.position_set.all()
            anzahl = positions.count()
            vol = self.column.volumen / anzahl
        return vol

    @property
    def products_on_position(self):
        products = self.product_set.all()
        return str(products)

    @property
    def total_order_cost(self):
        return "THEWALKINGDEADssssss"
