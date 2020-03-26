# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-10-21 08:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0317_legalcase_legal_case_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='inspection',
            name='legal_case',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inspection_legal_case', to='wildlifecompliance.LegalCase'),
        ),
        migrations.AddField(
            model_name='offence',
            name='legal_case',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='offence_legal_case', to='wildlifecompliance.LegalCase'),
        ),
    ]