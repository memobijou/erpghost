# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-09 17:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0010_auto_20180309_1510'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mission',
            name='verified',
        ),
    ]