# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-08 00:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0054_picklistproducts_missing_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='picklistproducts',
            name='ignore_stock',
            field=models.NullBooleanField(),
        ),
    ]
