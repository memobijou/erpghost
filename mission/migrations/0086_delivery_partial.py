# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-04 12:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0085_delivery_delivery_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='delivery',
            name='partial',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.Partial'),
        ),
    ]
