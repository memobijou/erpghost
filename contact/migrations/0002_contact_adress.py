# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-31 02:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('adress', '0001_initial'),
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='adress',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='contact', to='adress.Adress'),
        ),
    ]
