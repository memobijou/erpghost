# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-02-02 18:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Picklist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bestellungsnummer', models.CharField(max_length=13)),
                ('status', models.CharField(blank=True, max_length=25, null=True)),
                ('verified', models.NullBooleanField(choices=[(None, '----'), (True, 'Ja'), (False, 'Nein')])),
            ],
        ),
    ]
