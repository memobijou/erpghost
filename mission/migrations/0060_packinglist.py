# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-17 17:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0059_goodsissue_scan_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='PackingList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('packing_id', models.CharField(blank=True, max_length=200, null=True)),
                ('delivery', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.Delivery')),
            ],
        ),
    ]
