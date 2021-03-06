# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-30 21:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0002_auto_20161230_2032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='type',
            field=models.CharField(choices=[('type_two_dependend_fields', 'Two dependend fields'), ('type_yes_no', 'For "yes" or "no" answers'), ('type_multiselect_with_other', 'Unordered multiselect with "Other" option'), ('type_multiselect_ordered', 'Multiselect with ordering and "Other" option'), ('type_dependeend_question', 'Dependend question for TYPE_TWO_DEPENDEND_FIELDS type')], max_length=50, verbose_name='Question Type'),
        ),
        migrations.AlterField(
            model_name='surveyitem',
            name='survey',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='survey_items', to='survey.Survey'),
        ),
    ]
