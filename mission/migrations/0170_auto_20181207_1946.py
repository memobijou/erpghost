# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-12-07 18:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0169_auto_20181207_1910'),
    ]

    operations = [
        migrations.AddField(
            model_name='billingitem',
            name='brutto_price',
            field=models.FloatField(blank=True, null=True, verbose_name='Einzelpreis (Brutto)'),
        ),
        migrations.AddField(
            model_name='billingitem',
            name='discount',
            field=models.FloatField(blank=True, null=True, verbose_name='Rabatt'),
        ),
        migrations.AddField(
            model_name='billingitem',
            name='shipping_discount',
            field=models.FloatField(blank=True, null=True, verbose_name='Rabatt für Versand'),
        ),
        migrations.AddField(
            model_name='billingitem',
            name='shipping_price',
            field=models.FloatField(blank=True, null=True, verbose_name='Versandkosten'),
        ),
    ]
