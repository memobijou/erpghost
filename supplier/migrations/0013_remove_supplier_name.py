# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-21 22:54
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0012_auto_20180421_1901'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='supplier',
            name='name',
        ),
    ]
