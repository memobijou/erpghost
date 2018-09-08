# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-31 09:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0012_auto_20180811_1721'),
    ]

    operations = [
        migrations.AddField(
            model_name='apidata',
            name='access_token',
            field=models.CharField(blank=True, max_length=400, null=True, verbose_name='Zugriffstoken'),
        ),
        migrations.AddField(
            model_name='apidata',
            name='app_client_id',
            field=models.CharField(blank=True, max_length=400, null=True, verbose_name='Client ID'),
        ),
        migrations.AddField(
            model_name='apidata',
            name='authentication_key',
            field=models.CharField(blank=True, max_length=400, null=True, verbose_name='Authentifizierungstoken'),
        ),
        migrations.AddField(
            model_name='apidata',
            name='client_secret',
            field=models.CharField(blank=True, max_length=400, null=True, verbose_name='Client Secret'),
        ),
        migrations.AddField(
            model_name='apidata',
            name='refresh_token',
            field=models.CharField(blank=True, max_length=400, null=True, verbose_name='Aktualisierungstoken'),
        ),
    ]