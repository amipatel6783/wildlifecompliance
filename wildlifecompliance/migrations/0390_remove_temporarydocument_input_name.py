# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-01-20 00:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0389_auto_20200117_1738'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='temporarydocument',
            name='input_name',
        ),
    ]