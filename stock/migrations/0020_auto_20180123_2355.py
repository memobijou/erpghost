# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-23 23:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0019_stock_ignore_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='ignore_unique',
            field=models.CharField(blank=True, choices=[('IGNORE', 'Ja'), ('NOT_IGNORE', 'Nein')], max_length=250, null=True, verbose_name='Block'),
        ),
    ]
