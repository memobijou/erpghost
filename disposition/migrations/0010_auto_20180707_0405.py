# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-07 02:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('disposition', '0009_truckappointment_employees'),
    ]

    operations = [
        migrations.AlterField(
            model_name='truckappointment',
            name='arrival_date',
            field=models.DateField(null=True, verbose_name='Ankunftsdatum'),
        ),
    ]
