# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-11 21:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0139_auto_20180906_1913'),
        ('stock', '0038_position_name'),
        ('online', '0010_auto_20180911_1709'),
    ]

    operations = [
        migrations.CreateModel(
            name='RefillOrderInbookStock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(blank=True, null=True, verbose_name='Menge')),
                ('position', models.CharField(blank=True, max_length=200, null=True, verbose_name='Lagerplatz')),
                ('booked_in', models.NullBooleanField(verbose_name='Ausgebucht')),
                ('booked_in_amount', models.IntegerField(blank=True, null=True, verbose_name='Ausgebuchte Menge')),
                ('product_mission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.ProductMission')),
                ('refill_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='online.RefillOrder')),
                ('stock', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.Stock', verbose_name='Bestand')),
            ],
        ),
    ]
