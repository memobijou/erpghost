# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-14 17:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0101_auto_20180710_0337'),
    ]

    operations = [
        migrations.AlterField(
            model_name='packinglist',
            name='packing_id',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Verpacker ID'),
        ),
    ]