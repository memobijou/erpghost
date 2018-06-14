# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-03 21:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0060_productorder_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='shipping',
            field=models.CharField(blank=True, choices=[('Spedition', 'Spedition'), ('Dachser', 'Dachser'), ('DPD', 'DPD'), ('DHL', 'DHL')], max_length=200, null=True, verbose_name='Spedition'),
        ),
    ]