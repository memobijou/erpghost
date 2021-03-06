# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-26 03:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0134_picklist_online_delivery_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='picklist',
            name='tracking_number',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Tracking Nummer'),
        ),
        migrations.AlterField(
            model_name='picklistproducts',
            name='pick_list',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='mission.PickList'),
        ),
    ]
