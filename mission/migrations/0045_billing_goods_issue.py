# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-03 13:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0044_remove_deliverynote_billing'),
    ]

    operations = [
        migrations.AddField(
            model_name='billing',
            name='goods_issue',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.GoodsIssue'),
        ),
    ]
