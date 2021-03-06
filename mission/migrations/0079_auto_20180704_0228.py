# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-04 00:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0078_auto_20180704_0225'),
    ]

    operations = [
        migrations.AlterField(
            model_name='billing',
            name='delivery',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.Partial'),
        ),
        migrations.AlterField(
            model_name='deliverymissionproduct',
            name='delivery',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.Partial'),
        ),
        migrations.AlterField(
            model_name='deliverynote',
            name='delivery',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.Partial'),
        ),
        migrations.AlterField(
            model_name='ignorestockspicklist',
            name='delivery',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.Partial'),
        ),
        migrations.AlterField(
            model_name='packinglist',
            name='delivery',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.Partial'),
        ),
        migrations.AlterField(
            model_name='picklist',
            name='delivery',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.Partial'),
        ),
    ]
