# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-07 16:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('online', '0019_offer_sku_instance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='name',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Bezeichnung'),
        ),
    ]
