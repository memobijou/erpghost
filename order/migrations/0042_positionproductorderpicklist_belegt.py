# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-02-02 21:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0041_auto_20180202_2102'),
    ]

    operations = [
        migrations.AddField(
            model_name='positionproductorderpicklist',
            name='belegt',
            field=models.NullBooleanField(),
        ),
    ]
