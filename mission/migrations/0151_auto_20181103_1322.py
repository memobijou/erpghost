# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-03 12:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0150_auto_20181103_1244'),
    ]

    operations = [
        migrations.AddField(
            model_name='billing',
            name='created',
            field=models.DateTimeField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='billing',
            name='modified',
            field=models.DateTimeField(null=True),
        ),
    ]