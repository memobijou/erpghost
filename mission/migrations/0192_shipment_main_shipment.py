# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-01-02 05:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0191_shipment_billing'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipment',
            name='main_shipment',
            field=models.NullBooleanField(),
        ),
    ]
