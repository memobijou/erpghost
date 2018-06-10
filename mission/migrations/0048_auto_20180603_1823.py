# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-03 16:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0047_deliverynoteproductmission_billing'),
    ]

    operations = [
        migrations.AddField(
            model_name='billing',
            name='shipping_costs',
            field=models.FloatField(blank=True, max_length=200, null=True, verbose_name='Transportkosten'),
        ),
        migrations.AddField(
            model_name='billing',
            name='shipping_number_of_pieces',
            field=models.IntegerField(blank=True, null=True, verbose_name='Stückzahl Transport'),
        ),
        migrations.AddField(
            model_name='billing',
            name='transport_service',
            field=models.CharField(blank=True, choices=[('Dachser', 'Dachser'), ('DPD', 'DPD'), ('DHL', 'DHL')], max_length=200, null=True, verbose_name='Transportdienstleister'),
        ),
    ]
