# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-18 14:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0120_pickorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='picklist',
            name='pick_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.PickOrder'),
        ),
    ]
