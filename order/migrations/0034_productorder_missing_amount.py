# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-18 21:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('order', '0033_remove_productorder_missing_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='productorder',
            name='missing_amount',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
