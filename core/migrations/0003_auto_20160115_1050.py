# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-15 02:50
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_content_template'),
    ]

    operations = [
        migrations.RenameField(
            model_name='content',
            old_name='template',
            new_name='template_filename',
        ),
    ]
