from django.db import models



class Product(models.Model):
    ean = models.CharField(blank=True, null=False, max_length=13)

    def __str__(self):
        return self.ean



