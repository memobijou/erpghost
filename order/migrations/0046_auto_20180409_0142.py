# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-08 23:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0045_auto_20180316_1429'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='positionproductorder',
            name='positions',
        ),
        migrations.RemoveField(
            model_name='positionproductorder',
            name='productorder',
        ),
        migrations.RemoveField(
            model_name='positionproductorderpicklist',
            name='picklist',
        ),
        migrations.RemoveField(
            model_name='positionproductorderpicklist',
            name='positionproductorder',
        ),
        migrations.DeleteModel(
            name='PositionProductOrder',
        ),
        migrations.DeleteModel(
            name='PositionProductOrderPicklist',
        ),
    ]
