# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-17 09:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0007_auto_20180316_1659'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='supplier',
        ),
        migrations.AddField(
            model_name='product',
            name='part_number',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Herstellernummer'),
        ),
    ]