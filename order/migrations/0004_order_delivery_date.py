# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-14 08:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('order', '0003_remove_order_delivery_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
