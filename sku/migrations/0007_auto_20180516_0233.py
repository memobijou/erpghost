# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-16 00:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sku', '0006_sku_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sku',
            name='sku',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
