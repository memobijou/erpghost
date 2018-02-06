from django.db import models
from order.models import ProductOrder
from mission.models import Mission
from django.core.exceptions import ValidationError
# Create your models here.


class Reservation(models.Model):
    productorder = models.ForeignKey(ProductOrder, on_delete=models.CASCADE,related_name='produtcorders')
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    amount = models.IntegerField(null=False, blank=False)
    CHOICES = (
        (None, "----"),
        (True, "Ja"),
        (False, "Nein")
    )
    status = models.NullBooleanField(choices=CHOICES)

    def __str__(self):
        return str(self.productorder)

    def clean(self):
        product_order = self.productorder
        free_amount = product_order.free_amount()
        if free_amount < self.amount:
            raise ValidationError("Menge ist größer als freie menge ")
        elif self.amount == 0:
            raise ValidationError("Keine Menge")
