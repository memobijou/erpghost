# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-11 03:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0038_position_name'),
        ('online', '0007_auto_20180911_0251'),
    ]

    operations = [
        migrations.AddField(
            model_name='refillorderoutbookstock',
            name='stock',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.Stock', verbose_name='Bestand'),
        ),
    ]
