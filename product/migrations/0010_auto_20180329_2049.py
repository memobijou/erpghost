# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-29 18:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0009_auto_20180320_0959'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Beschreibung'),
        ),
        migrations.AddField(
            model_name='product',
            name='height',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='length',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='short_description',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Kurzbeschreibung'),
        ),
        migrations.AddField(
            model_name='product',
            name='title',
            field=models.CharField(blank=True, default='', max_length=500, null=True, verbose_name='Titel'),
        ),
        migrations.AddField(
            model_name='product',
            name='width',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
    ]
