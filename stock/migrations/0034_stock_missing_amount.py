# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-10 19:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0033_auto_20180527_0212'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='missing_amount',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
