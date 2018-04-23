# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-22 18:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adress', '0004_adress_place'),
        ('order', '0049_auto_20180422_1113'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='adress.Adress'),
        ),
    ]