# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-12-01 04:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0045_rebookorderitem_destination_stock'),
    ]

    operations = [
        migrations.AddField(
            model_name='rebookorderitem',
            name='rebooked_amount',
            field=models.IntegerField(blank=True, null=True, verbose_name='Tatsächliche Umbuchmenge'),
        ),
    ]