# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-27 04:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0068_auto_20180627_0625'),
    ]

    operations = [
        migrations.CreateModel(
            name='Truck',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arrival_date', models.DateField(blank=True, null=True, verbose_name='Ankunftsdatum')),
                ('arrival_time', models.TimeField(blank=True, null=True, verbose_name='Ankunftszeit')),
            ],
        ),
    ]
