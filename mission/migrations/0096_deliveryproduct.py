# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-08 01:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0095_truck_outgoing'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(blank=True, null=True, verbose_name='Menge')),
                ('delivery', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.Delivery')),
                ('product_mission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.ProductMission')),
            ],
        ),
    ]
