# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-12-21 01:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0580_auto_20211220_1057'),
    ]

    operations = [
        migrations.AlterField(
            model_name='callemail',
            name='dead',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='callemail',
            name='euthanise',
            field=models.NullBooleanField(),
        ),
    ]