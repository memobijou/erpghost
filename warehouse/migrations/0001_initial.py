# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-24 15:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gesamt_kubik', models.CharField(blank=True, max_length=13)),
            ],
        ),
    ]
