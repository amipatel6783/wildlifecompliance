# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-01-13 06:21
from __future__ import unicode_literals

from django.db import migrations
import ledger.accounts.models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0024_organisation_email'),
        ('wildlifecompliance', '0378_merge_20200113_1323'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComplianceManagementEmailUser',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('accounts.emailuser',),
            managers=[
                ('objects', ledger.accounts.models.EmailUserManager()),
            ],
        ),
    ]
