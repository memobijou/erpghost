# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-14 18:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('online', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='name',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Channel'),
        ),
    ]
