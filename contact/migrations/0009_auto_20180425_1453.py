# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-25 12:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0008_auto_20180425_0749'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='billing_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='billing_contact', to='adress.Adress'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='delivery_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='delivery_contact', to='adress.Adress'),
        ),
    ]
