# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-12-05 22:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0165_mission_none_sku_products_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='mission',
            name='ignore_pickorder',
            field=models.NullBooleanField(verbose_name='Kein Pickauftrag erstellen'),
        ),
    ]
