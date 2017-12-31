# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-27 00:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0003_product'),
        ('position', '0002_positionproduct'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='products',
            field=models.ManyToManyField(through='position.PositionProduct', to='product.Product'),
        ),
    ]
