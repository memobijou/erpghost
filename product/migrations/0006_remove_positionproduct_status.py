# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-13 15:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_positionproduct_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='positionproduct',
            name='status',
        ),
    ]
