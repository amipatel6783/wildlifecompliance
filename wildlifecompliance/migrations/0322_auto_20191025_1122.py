# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-10-25 03:22
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0321_remove_sectionregulation_amount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='allegedcommittedoffence',
            name='reason_for_removal',
        ),
        migrations.RemoveField(
            model_name='allegedcommittedoffence',
            name='removed',
        ),
        migrations.RemoveField(
            model_name='allegedcommittedoffence',
            name='removed_by',
        ),
    ]
