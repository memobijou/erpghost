# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-03 23:54
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0074_remove_goodsissue_delivery'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='goodsissuedeliverymissionproduct',
            name='delivery_mission_product',
        ),
        migrations.RemoveField(
            model_name='goodsissuedeliverymissionproduct',
            name='goods_issue',
        ),
        migrations.DeleteModel(
            name='GoodsIssueDeliveryMissionProduct',
        ),
    ]
