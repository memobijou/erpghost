# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-23 02:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0003_contact_company_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank', models.CharField(blank=True, max_length=200, null=True, verbose_name='Bank')),
                ('bic', models.CharField(blank=True, max_length=200, null=True, verbose_name='BIC')),
                ('iban', models.CharField(blank=True, max_length=200, null=True, verbose_name='IBAN')),
            ],
        ),
        migrations.AddField(
            model_name='contact',
            name='fax',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Fax'),
        ),
        migrations.AddField(
            model_name='contact',
            name='website',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Webseite'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='email',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='skype_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='telefon',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Telefon'),
        ),
        migrations.AddField(
            model_name='contact',
            name='bank',
            field=models.ManyToManyField(to='contact.Bank'),
        ),
    ]
