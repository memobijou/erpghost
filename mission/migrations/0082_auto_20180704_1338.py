# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-04 11:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0081_auto_20180704_1249'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='realamount',
            name='billing',
        ),
        migrations.RemoveField(
            model_name='realamount',
            name='delivery_note',
        ),
        migrations.RemoveField(
            model_name='realamount',
            name='product_mission',
        ),
        migrations.DeleteModel(
            name='RealAmount',
        ),
    ]
