# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-20 08:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_auto_20180317_0939'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='ean',
            field=models.CharField(blank=True, max_length=200, verbose_name='EAN'),
        ),
    ]
