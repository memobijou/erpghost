# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-26 19:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('column', '0003_column_positions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='column',
            name='positions',
        ),
    ]
