# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-15 22:51
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0115_auto_20180815_1235'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='picklist',
            name='accepted',
        ),
    ]
