# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-07 16:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0052_auto_20180604_0607'),
    ]

    operations = [
        migrations.AddField(
            model_name='picklistproducts',
            name='confirmed',
            field=models.NullBooleanField(verbose_name='Bestätigt'),
        ),
    ]