# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-14 10:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0113_auto_20180808_0255'),
    ]

    operations = [
        migrations.AddField(
            model_name='picklistproducts',
            name='picked',
            field=models.NullBooleanField(verbose_name='Gepickt'),
        ),
    ]
