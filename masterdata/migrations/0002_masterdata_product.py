# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-24 23:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('product', '0003_product'),
        ('masterdata', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='masterdata',
            name='product',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                       to='product.Product'),
        ),
    ]
