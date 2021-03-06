# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-04 00:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0076_delete_goodsissue'),
    ]

    operations = [
        migrations.AlterField(
            model_name='billing',
            name='delivery',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='deliverymissionproduct',
            name='delivery',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='deliverynote',
            name='delivery',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ignorestockspicklist',
            name='delivery',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='packinglist',
            name='delivery',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='picklist',
            name='delivery',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
