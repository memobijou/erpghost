# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-28 21:17
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stock', '0040_auto_20181023_0243'),
    ]

    operations = [
        migrations.CreateModel(
            name='RebookOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='')),
            ],
        ),
        migrations.CreateModel(
            name='RebookOrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(blank=True, null=True, verbose_name='Umbuchmenge')),
                ('rebooked', models.NullBooleanField(verbose_name='Umgebucht')),
                ('rebook_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.RebookOrder')),
                ('stock', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.Stock', verbose_name='Bestand')),
            ],
        ),
    ]