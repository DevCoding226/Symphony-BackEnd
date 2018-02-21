# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-02-21 10:11
from __future__ import unicode_literals

from django.db import migrations


def delete_empty_answers(apps, schema_editor):
    Answer = apps.get_model('survey', 'Answer')
    Answer.objects.filter(body='').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0035_question_available_if'),
    ]

    operations = [
        migrations.RunPython(delete_empty_answers)
    ]
