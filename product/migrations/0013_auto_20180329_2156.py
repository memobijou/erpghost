# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-29 19:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0012_product_brand'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=200, verbose_name='Markenname')),
            ],
        ),
        migrations.RemoveField(
            model_name='product',
            name='brand',
        ),
    ]
