# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-31 03:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('order', '0023_auto_20171231_0334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceorder',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.Invoice'),
        ),
    ]
