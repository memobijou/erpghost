from django.db import models

# Create your models here.


class OnlinePositionPrefix(models.Model):
    class Meta:
        ordering = ('pk',)

    prefix = models.CharField(null=True, blank=False, max_length=200, verbose_name="Lagerpositionen Prefix",
                              help_text="<div class='help-block'>Geben Sie einen Prefix ein von bereits erstellten "
                                        "Lagerpositionen und alle Lagerpositionen mit dem Prefix werden für den "
                                        "Onlinehandel freigegeben.</div>")
