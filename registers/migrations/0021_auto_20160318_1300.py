# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-18 05:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registers', '0020_auto_20160318_1207'),
    ]

    operations = [
        migrations.AddField(
            model_name='hardware',
            name='location',
            field=models.ForeignKey(blank=True, help_text='Physical location', null=True, on_delete=django.db.models.deletion.PROTECT, to='registers.Location'),
        ),
        migrations.AlterField(
            model_name='hardware',
            name='os',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='registers.Software'),
        ),
    ]
