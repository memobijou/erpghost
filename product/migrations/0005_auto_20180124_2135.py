# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-24 21:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_auto_20171228_2347'),
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
            model_name='product',
            name='positions',
        ),
        migrations.DeleteModel(
            name='PositionProduct',
        ),
    ]