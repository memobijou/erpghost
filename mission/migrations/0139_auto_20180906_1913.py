# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-06 17:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0138_mission_shipped'),
    ]

    operations = [
        migrations.AddField(
            model_name='mission',
            name='delivery_date_from',
            field=models.DateField(blank=True, null=True, verbose_name='Lieferdatum von'),
        ),
        migrations.AddField(
            model_name='mission',
            name='delivery_date_to',
            field=models.DateField(blank=True, null=True, verbose_name='Lieferdatum bis'),
        ),
    ]
