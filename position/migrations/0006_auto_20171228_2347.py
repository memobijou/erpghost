# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-28 23:47
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('position', '0005_auto_20171228_1955'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='positionproduct',
            name='positions',
        ),
        migrations.RemoveField(
            model_name='positionproduct',
            name='products',
        ),
        migrations.RemoveField(
            model_name='position',
            name='products',
        ),
        migrations.DeleteModel(
            name='PositionProduct',
        ),
    ]
