from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    celery_import_task_id = models.CharField(max_length=400, null=True, blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile") is False:
        Profile.objects.create(user=instance)
    instance.refresh_from_db()
    instance.profile.save()


class TruckAppointment(models.Model):
    truck = models.ForeignKey("mission.Truck", null=True, blank=True)
    arrival_date = models.DateField(null=True, blank=False, verbose_name="Ankunftsdatum")

    arrival_time_start = models.TimeField(null=True, blank=True, verbose_name="Ankunftszeit von")
    arrival_time_end = models.TimeField(null=True, blank=True, verbose_name="Ankunftszeit bis")

    employees = models.ManyToManyField("disposition.Employee", blank=True)


class TransportService(models.Model):
    name = models.CharField(null=True, blank=False, max_length=200, verbose_name="Bezeichnung")


type_choices = [("national", "Deutschland"), ("foreign_country", "Ausland")]


class BusinessAccount(models.Model):
    username = models.CharField(null=True, blank=True, max_length=200, verbose_name="Benutzername")
    password_encrypted = models.CharField(null=True, blank=True, max_length=200)
    transport_service = models.ForeignKey("disposition.TransportService", null=True, blank=True)
    client = models.ForeignKey("client.Client", null=True, blank=True, verbose_name="Mandant")
    type = models.CharField(null=True, blank=False, verbose_name="Art", choices=type_choices, max_length=200)
