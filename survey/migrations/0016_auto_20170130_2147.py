# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-30 21:47
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0015_auto_20170126_1229'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
