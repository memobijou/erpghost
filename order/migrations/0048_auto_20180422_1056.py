# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-22 08:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0047_order_terms_of_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='terms_of_delivery',
            field=models.CharField(blank=True, choices=[('DDP - Frei Haus verzollt', 'DDP - Frei Haus verzollt'), ('CIF - Frei Haus', 'CIF - Frei Haus'), ('CIP - Frei Haus', 'CIP - Frei Haus'), ('EXW - Ab Werk', 'EXW - Ab Werk')], max_length=200, null=True, verbose_name='Lieferkonditionen'),
        ),
        migrations.AlterField(
            model_name='order',
            name='terms_of_payment',
            field=models.CharField(blank=True, choices=[('Innerhalb 30 Tage netto, ohne Abzug', 'Innerhalb 30 Tage netto, ohne Abzug'), ('Sofort nach Erhalt, ohne Abzug', 'Sofort nach Erhalt, ohne Abzug'), ('Innerhalb 14 Tage netto, ohne Abzug', 'Innerhalb 14 Tage netto, ohne Abzug'), ('30 Tage netto, 14 Tage 3% Skonto', '30 Tage netto, 14 Tage 3% Skonto'), ('7 Tage netto', '7 Tage netto'), ('Vorkasse', 'Vorkasse'), ('innerhalb 45 Tage 3% Skonto', 'innerhalb 45 Tage 3% Skonto'), ('innerhalb 60 Tagen, ohne Abzug', 'innerhalb 60 Tagen, ohne Abzug'), ('innerhalb 21 Tage, ohne Abzug', 'innerhalb 21 Tage, ohne Abzug'), ('15 Tage 3% Skonto, 45 Tage Valuta', '15 Tage 3% Skonto, 45 Tage Valuta'), ('innerhalb 90 Tage, ohne Abzug', 'innerhalb 90 Tage, ohne Abzug'), ('10 Tage netto', '10 Tage netto')], max_length=200, null=True, verbose_name='Zahlungsbedingung'),
        ),
    ]
