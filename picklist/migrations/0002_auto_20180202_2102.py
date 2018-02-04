# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-02-02 21:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('picklist', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='picklist',
            name='verified',
        ),
        migrations.AddField(
            model_name='picklist',
            name='comment',
            field=models.NullBooleanField(choices=[(None, '----'), (True, 'ok'), (False, 'nicht ok')]),
        ),
        migrations.AddField(
            model_name='picklist',
            name='complete',
            field=models.NullBooleanField(default=False),
        ),
        migrations.AddField(
            model_name='picklist',
            name='end_time',
            field=models.CharField(default='asdf', max_length=13),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='picklist',
            name='start_time',
            field=models.CharField(default='asdf', max_length=13),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='picklist',
            name='status',
            field=models.NullBooleanField(choices=[(None, '----'), (True, 'Fertig'), (False, 'in bearbeitung')]),
        ),
    ]
