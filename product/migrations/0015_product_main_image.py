# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-29 21:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0014_auto_20180329_2204'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='main_image',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='Bild'),
        ),
    ]
