# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-11 15:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('online', '0008_refillorderoutbookstock_stock'),
    ]

    operations = [
        migrations.RenameField(
            model_name='refillorder',
            old_name='completed',
            new_name='booked_out',
        ),
    ]
