# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-05 10:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0109_productmission_online_shipped_amount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mission',
            name='shipping_costs',
        ),
        migrations.RemoveField(
            model_name='mission',
            name='shipping_number_of_pieces',
        ),
        migrations.AddField(
            model_name='mission',
            name='tracking_number',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Tracking Nummer'),
        ),
        migrations.AlterField(
            model_name='mission',
            name='shipping',
            field=models.CharField(blank=True, choices=[('DHL', 'DHL'), ('DPD', 'DPD')], max_length=200, null=True, verbose_name='Spedition'),
        ),
    ]
