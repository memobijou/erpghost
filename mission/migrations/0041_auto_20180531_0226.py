# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-31 00:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0040_goodsissuedeliverymissionproduct_confirmed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goodsissuedeliverymissionproduct',
            name='amount',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='Menge'),
        ),
        migrations.AlterField(
            model_name='goodsissuedeliverymissionproduct',
            name='missing_amount',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='Fehlende Menge'),
        ),
    ]