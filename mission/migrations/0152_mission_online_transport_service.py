# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-03 14:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('disposition', '0020_profile_celery_import_task_id'),
        ('mission', '0151_auto_20181103_1322'),
    ]

    operations = [
        migrations.AddField(
            model_name='mission',
            name='online_transport_service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='disposition.TransportService'),
        ),
    ]
