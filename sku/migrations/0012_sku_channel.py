# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-24 06:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('online', '0015_offer'),
        ('sku', '0011_sku_main_sku'),
    ]

    operations = [
        migrations.AddField(
            model_name='sku',
            name='channel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='online.Channel'),
        ),
    ]
