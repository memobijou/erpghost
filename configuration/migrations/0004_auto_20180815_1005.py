# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-15 08:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0003_auto_20180814_2354'),
    ]

    operations = [
        migrations.AlterField(
            model_name='onlinepositionprefix',
            name='prefix',
            field=models.CharField(help_text="<div class='help-block'>Geben Sie einen Prefix ein von bereits erstellten Lagerpositionen und alle Lagerpositionen mit dem Prefix werden für den Onlinehandel freigegeben.</div>", max_length=200, null=True, verbose_name='Lagerpositionen Prefix'),
        ),
    ]
