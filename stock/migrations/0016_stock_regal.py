# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-09 20:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('stock', '0015_auto_20180108_2239'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='regal',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
