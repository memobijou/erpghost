# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-12-10 00:34
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0178_auto_20181210_0133'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mission',
            options={'ordering': ['purchased_date']},
        ),
    ]