# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-03 14:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0045_billing_goods_issue'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='delivery',
            name='billing',
        ),
    ]