# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-04 11:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0082_auto_20180704_1338'),
    ]

    operations = [
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('billing', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.Billing')),
                ('delivery_note', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.DeliveryNote')),
            ],
        ),
    ]
