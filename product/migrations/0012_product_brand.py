# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-29 19:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0011_auto_20180329_2124'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Markenname'),
        ),
    ]
