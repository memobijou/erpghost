# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-26 19:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('position', '0001_initial'),
        ('column', '0004_remove_column_positions'),
    ]

    operations = [
        migrations.CreateModel(
            name='ColumnPosition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('columns', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='column.Column')),
                ('positions', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='position.Position')),
            ],
        ),
    ]