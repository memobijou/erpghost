# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-25 19:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0037_auto_20180125_1921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='positionproductorder',
            name='positions',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='position.Position'),
        ),
    ]
