# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-25 13:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0132_mission_online_delivery_note'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mission',
            name='online_delivery_note',
        ),
    ]
