# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2018-09-17 12:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logsforhumans', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='humanlog',
            name='object_id',
            field=models.CharField(max_length=512),
        ),
    ]