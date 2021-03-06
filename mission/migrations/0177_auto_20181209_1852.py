# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-12-09 17:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sku', '0015_auto_20181107_2310'),
        ('mission', '0176_productmission_packing_unit'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mission',
            name='skus',
        ),
        migrations.AddField(
            model_name='productmission',
            name='internal_sku',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='internal_skus', to='sku.Sku', verbose_name='Interne Sku'),
        ),
        migrations.AlterField(
            model_name='productmission',
            name='sku',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='sku.Sku', verbose_name='Online Sku'),
        ),
    ]
