# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-12 02:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0022_auto_20180510_1939'),
    ]

    operations = [
        migrations.AddField(
            model_name='realamount',
            name='confirmed',
            field=models.NullBooleanField(choices=[(None, '----'), (True, 'Ja'), (False, 'Nein')], verbose_name='Bestätigt'),
        ),
    ]
