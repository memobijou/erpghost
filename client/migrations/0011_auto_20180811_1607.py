# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-11 14:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0010_auto_20180811_1606'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apidata',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='client.Client', verbose_name='Mandant'),
        ),
    ]
