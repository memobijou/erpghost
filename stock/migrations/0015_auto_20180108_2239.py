# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-08 22:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('stock', '0014_auto_20180106_1711'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='box',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
