# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-04 15:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0152_mission_online_transport_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='productmission',
            name='shipping_price',
            field=models.FloatField(blank=True, null=True, verbose_name='Versandkosten'),
        ),
    ]
