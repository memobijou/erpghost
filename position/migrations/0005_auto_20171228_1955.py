# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-28 19:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('position', '0004_auto_20171227_0057'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='columnposition',
            name='columns',
        ),
        migrations.RemoveField(
            model_name='columnposition',
            name='positions',
        ),
        migrations.RemoveField(
            model_name='position',
            name='columns',
        ),
        migrations.DeleteModel(
            name='ColumnPosition',
        ),
    ]
