# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-27 04:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mission', '0028_billing_deliverynote'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='realamount',
            name='billing_number',
        ),
        migrations.RemoveField(
            model_name='realamount',
            name='delivery_note_number',
        ),
        migrations.AddField(
            model_name='realamount',
            name='billing',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.Billing'),
        ),
        migrations.AddField(
            model_name='realamount',
            name='delivery_note',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mission.DeliveryNote'),
        ),
    ]
