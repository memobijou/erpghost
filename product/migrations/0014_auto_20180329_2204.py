# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-29 20:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0013_auto_20180329_2156'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='brandname',
            field=models.CharField(blank=True, default='', max_length=500, null=True, verbose_name='Markenname'),
        ),
        migrations.AlterField(
            model_name='product',
            name='manufacturer',
            field=models.CharField(blank=True, default='', max_length=500, null=True, verbose_name='Hersteller'),
        ),
    ]
