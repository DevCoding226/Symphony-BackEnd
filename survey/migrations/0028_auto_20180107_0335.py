# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-01-07 03:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0027_populate_survey_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='survey',
            name='slug',
            field=models.SlugField(unique=True, verbose_name='Survey slug'),
        ),
    ]
