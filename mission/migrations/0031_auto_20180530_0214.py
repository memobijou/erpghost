# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-30 00:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0030_auto_20180530_0148'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deliverynote',
            name='amount',
        ),
        migrations.RemoveField(
            model_name='deliverynote',
            name='missing_amount',
        ),
        migrations.RemoveField(
            model_name='deliverynote',
            name='product_mission',
        ),
    ]
