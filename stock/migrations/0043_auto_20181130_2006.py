# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-30 19:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0042_auto_20181128_2312'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rebookorder',
            name='all_rebooked',
        ),
        migrations.AddField(
            model_name='rebookorder',
            name='completed',
            field=models.NullBooleanField(verbose_name='Abgeschloßen'),
        ),
    ]
