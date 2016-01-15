# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-15 02:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='content',
            name='template',
            field=models.CharField(choices=[('content.html', 'content.html'), ('f6-content.html', 'f6-content.html')], default='content.html', max_length=64),
        ),
    ]
