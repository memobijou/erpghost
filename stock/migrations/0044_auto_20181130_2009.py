# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-30 19:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0043_auto_20181130_2006'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rebookorder',
            options={'ordering': ['id']},
        ),
    ]