# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-07-26 08:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0264_merge_20190726_1101'),
    ]

    operations = [
        migrations.AddField(
            model_name='offence',
            name='lodgement_number',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]