from django.db import models

# Create your models here.


class Channel(models.Model):
    name = models.CharField(null=True, blank=True, max_length=200, verbose_name="Channel")
