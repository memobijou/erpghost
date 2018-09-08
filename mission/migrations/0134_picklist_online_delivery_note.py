# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-25 13:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0133_remove_mission_online_delivery_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='picklist',
            name='online_delivery_note',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.DeliveryNote'),
        ),
    ]
