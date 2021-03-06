# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-10 22:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0003_auto_20161230_2113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='type',
            field=models.CharField(choices=[('type_two_dependend_fields', 'Two dependend fields'), ('type_yes_no', 'For "yes" or "no" answers'), ('type_multiselect_with_other', 'Unordered multiselect with "Other" option'), ('type_multiselect_ordered', 'Multiselect with ordering and "Other" option'), ('type_dependeend_question', 'Dependend question for TYPE_TWO_DEPENDEND_FIELDS type'), ('type_simple_input', 'Simple input field'), ('type_yes_no_jumping', 'Yes-No, that allow to jump to the certain question')], max_length=50, verbose_name='Question Type'),
        ),
    ]
