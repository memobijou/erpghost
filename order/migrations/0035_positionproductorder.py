# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-24 21:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('position', '0007_position_column'),
        ('order', '0034_productorder_missing_amount'),
    ]

    operations = [
        migrations.CreateModel(
            name='PositionProductOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(default=0)),
                ('positions', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='position.Position')),
                ('productorder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order.ProductOrder')),
            ],
        ),
    ]