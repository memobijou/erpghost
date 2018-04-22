from django.db import models
# Create your models here.


class Picklist(models.Model):
    bestellungsnummer = models.CharField(max_length=13)
    status = models.CharField(max_length=25, null=True, blank=True)
    CHOICES = (
        (None, "----"),
        (True, "ok"),
        (False, "nicht ok")
    )
    comment = models.NullBooleanField(choices=CHOICES)
    complete = models.NullBooleanField(default=False)
    end_time = models.CharField(max_length=13)
    start_time = models.CharField(max_length=13)


    CHOICES_status = (
        (None, "----"),
        (True, "Fertig"),
        (False, "in bearbeitung")
    )
    status = models.NullBooleanField(choices=CHOICES_status)

    def __str__(self):
        return str(self.status) + str(self.bestellungsnummer)
