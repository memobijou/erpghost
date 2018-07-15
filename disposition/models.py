from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Employee(models.Model):
    class Meta:
        ordering = ["pk"]

    user = models.OneToOneField(User, null=True, blank=True)

    def __str__(self):
        if self.user.profile:
            return f"{self.user.profile.first_name} {self.user.profile.last_name}"
        return self.user.username


class Profile(models.Model):
    profile_image = models.ImageField(verbose_name="Profilbild", null=True, blank=True)
    first_name = models.CharField(verbose_name="Vorname", null=True, blank=True, max_length=200)
    last_name = models.CharField(verbose_name="Nachname", null=True, blank=True, max_length=200)
    user = models.OneToOneField(User, null=True, blank=True)


class TruckAppointment(models.Model):
    truck = models.ForeignKey("mission.Truck", null=True, blank=True)
    arrival_date = models.DateField(null=True, blank=False, verbose_name="Ankunftsdatum")

    arrival_time_start = models.TimeField(null=True, blank=True, verbose_name="Ankunftszeit von")
    arrival_time_end = models.TimeField(null=True, blank=True, verbose_name="Ankunftszeit bis")

    employees = models.ManyToManyField("disposition.Employee", blank=True)
