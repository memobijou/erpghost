# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-24 23:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Masterdata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('height', models.FloatField(blank=True, default=None, null=True)),
                ('width', models.FloatField(blank=True, default=None, null=True)),
                ('length', models.FloatField(blank=True, default=None, null=True)),
            ],
        ),
    ]
