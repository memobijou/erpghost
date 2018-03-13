# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-09 14:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='customer', to='contact.Contact', verbose_name='Kontaktdaten'),
        ),
    ]
