# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-22 15:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0002_contact_adress'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='company_image',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='Firmenlogo'),
        ),
    ]
