# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-20 10:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0011_contact_website_conditions_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='first_name_last_name',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Name'),
        ),
    ]
