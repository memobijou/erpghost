# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-15 23:22
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0162_productmission_online_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productmission',
            old_name='no_match_identifier',
            new_name='online_identifier',
        ),
    ]
