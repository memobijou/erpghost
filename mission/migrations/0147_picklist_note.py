# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-30 00:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0146_auto_20181023_1321'),
    ]

    operations = [
        migrations.AddField(
            model_name='picklist',
            name='note',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
    ]
