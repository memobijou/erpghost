# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-09 22:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('disposition', '0014_businessaccount_transport_service'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessaccount',
            name='username',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Benutzername'),
        ),
        migrations.AlterField(
            model_name='transportservice',
            name='name',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Bezeichnung'),
        ),
    ]