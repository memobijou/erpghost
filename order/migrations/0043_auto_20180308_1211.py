# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-08 12:11
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0042_positionproductorderpicklist_belegt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='delivery_date',
            field=models.DateField(default=datetime.date.today, verbose_name='Lieferdatum'),
        ),
        migrations.AlterField(
            model_name='order',
            name='ordernumber',
            field=models.CharField(blank=True, max_length=13, verbose_name='Bestellnummer'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(blank=True, default='OFFEN', max_length=25, null=True, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='order',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order', to='supplier.Supplier', verbose_name='Lieferant'),
        ),
        migrations.AlterField(
            model_name='order',
            name='verified',
            field=models.NullBooleanField(choices=[(None, '----'), (True, 'Ja'), (False, 'Nein')], verbose_name='Akzeptiert'),
        ),
    ]
