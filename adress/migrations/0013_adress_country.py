# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-12 01:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adress', '0012_auto_20180922_0119'),
    ]

    operations = [
        migrations.AddField(
            model_name='adress',
            name='country',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Land'),
        ),
    ]
