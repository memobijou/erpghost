# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-07 22:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sku', '0014_auto_20181107_2310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sku',
            name='state',
            field=models.CharField(max_length=200, null=True, verbose_name='Zustand'),
        ),
    ]