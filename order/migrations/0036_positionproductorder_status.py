# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-24 21:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0035_positionproductorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='positionproductorder',
            name='status',
            field=models.NullBooleanField(choices=[(None, '----'), (True, 'auf der Position'), (False, 'auf dem Weg')]),
        ),
    ]