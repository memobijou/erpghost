# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-14 15:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('disposition', '0021_businessaccount_channel'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='businessaccount',
            name='channel',
        ),
    ]
