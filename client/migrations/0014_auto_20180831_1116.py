# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-31 09:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0013_auto_20180831_1115'),
    ]

    operations = [
        migrations.RenameField(
            model_name='apidata',
            old_name='authentication_key',
            new_name='authentication_token',
        ),
    ]
