from django.db import models


class Invoice(models.Model):
    bezeichnung = models.CharField(blank=True, null=False, max_length=13)
    text_middle = models.CharField(blank=True, null=False, max_length=50)
    text_down = models.CharField(blank=True, null=False, max_length=50)
    text_extra = models.CharField(blank=True, null=False, max_length=50)
    text_tbl = models.CharField(blank=True, null=False, max_length=50)

    # date = models.CharField(blank=True, null=False, max_length=50)

    def __str__(self):
        return self.bezeichnung
