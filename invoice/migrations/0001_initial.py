# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-30 15:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bezeichnung', models.CharField(blank=True, max_length=13)),
                ('text_middle', models.CharField(blank=True, max_length=50)),
                ('text_down', models.CharField(blank=True, max_length=50)),
                ('text_extra', models.CharField(blank=True, max_length=50)),
                ('text_tbl', models.CharField(blank=True, max_length=50)),
                ('date', models.CharField(blank=True, max_length=50)),
            ],
        ),
    ]
