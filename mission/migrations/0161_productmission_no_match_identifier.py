# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-15 22:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0160_auto_20181114_1753'),
    ]

    operations = [
        migrations.AddField(
            model_name='productmission',
            name='no_match_identifier',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
