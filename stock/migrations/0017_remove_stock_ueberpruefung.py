# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-09 20:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('stock', '0016_stock_regal'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stock',
            name='ueberpruefung',
        ),
    ]
