# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-06 16:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('stock', '0011_auto_20180106_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='ean_vollstaendig',
            field=models.CharField(max_length=250),
        ),
    ]
