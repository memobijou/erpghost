# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-25 18:45
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0064_auto_20180617_2341'),
    ]

    operations = [
        migrations.AddField(
            model_name='billing',
            name='delivery_date',
            field=models.DateField(default=datetime.date.today, verbose_name='Lieferdatum'),
        ),
        migrations.AddField(
            model_name='deliverynote',
            name='delivery_date',
            field=models.DateField(default=datetime.date.today, verbose_name='Lieferdatum'),
        ),
    ]