# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-24 22:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0144_billingproductmission'),
    ]

    operations = [
        migrations.AddField(
            model_name='mission',
            name='online_transport_cost',
            field=models.FloatField(blank=True, null=True, verbose_name='Transportkosten'),
        ),
    ]