# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-27 00:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0032_stock_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.Product'),
        ),
    ]
