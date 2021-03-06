# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-17 10:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0002_auto_20151217_0705'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departmentuser',
            name='employee_id',
            field=models.CharField(blank=True, max_length=128, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='departmentuser',
            name='org_unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='registers.OrgUnit'),
        ),
    ]
