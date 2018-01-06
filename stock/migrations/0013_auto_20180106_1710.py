# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-06 17:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0012_auto_20180106_1659'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='aufnahme_datum',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='bereich',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='bestand',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='box',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='ean_upc',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='karton',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='lagerplatz',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='name',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='scanner',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='ueberpruefung',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='zustand',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
