# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-14 13:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('online', '0022_auto_20181110_1637'),
        ('disposition', '0020_profile_celery_import_task_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessaccount',
            name='channel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='online.Channel', verbose_name='Verkaufskanal'),
        ),
    ]
