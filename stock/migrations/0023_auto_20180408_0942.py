# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-08 07:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0022_auto_20180407_2319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='ean_vollstaendig',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='EAN'),
        ),
    ]
