# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-10 12:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('online', '0020_auto_20181107_1745'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offer',
            name='sku_instance',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sku.Sku'),
        ),
    ]
