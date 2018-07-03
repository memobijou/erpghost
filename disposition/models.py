from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Employee(models.Model):
    class Meta:
        ordering = ["pk"]

    user = models.OneToOneField(User, null=True, blank=True)

    def __str__(self):
        return self.user.username


class Profile(models.Model):
    profile_image = models.ImageField(verbose_name="Profilbild")
    user = models.OneToOneField(User, null=True, blank=True)
