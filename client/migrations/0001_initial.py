# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-30 17:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=13)),
                ('strasse', models.CharField(blank=True, max_length=13)),
                ('ort_id', models.CharField(blank=True, max_length=13)),
            ],
        ),
    ]
