# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-27 04:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0069_truck'),
    ]

    operations = [
        migrations.AddField(
            model_name='truck',
            name='delivery_note',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.DeliveryNote'),
        ),
    ]
