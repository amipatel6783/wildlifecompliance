# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-12-24 05:49
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0357_auto_20191224_1345'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='remediationactiontaken',
            name='remediation_action',
        ),
        migrations.RemoveField(
            model_name='remediationactiontakendocument',
            name='remediation_action_taken',
        ),
        migrations.DeleteModel(
            name='RemediationActionTaken',
        ),
        migrations.DeleteModel(
            name='RemediationActionTakenDocument',
        ),
    ]