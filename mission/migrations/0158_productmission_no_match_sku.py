# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-13 05:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0157_auto_20181112_1754'),
    ]

    operations = [
        migrations.AddField(
            model_name='productmission',
            name='no_match_sku',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
