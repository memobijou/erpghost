# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-26 00:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0019_singleproduct'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='single_product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='product.SingleProduct'),
        ),
    ]
