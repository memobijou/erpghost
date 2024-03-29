# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-27 15:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0015_mission_delivery_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='mission',
            name='billing_number',
            field=models.CharField(blank=True, max_length=200, verbose_name='Rechnungsnummer'),
        ),
        migrations.AlterField(
            model_name='mission',
            name='mission_number',
            field=models.CharField(blank=True, max_length=200, verbose_name='Auftragsnummer'),
        ),
        migrations.AlterField(
            model_name='mission',
            name='status',
            field=models.CharField(blank=True, default='OFFEN', max_length=200, null=True, verbose_name='Status'),
        ),
    ]
