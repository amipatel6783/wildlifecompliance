# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-09-06 07:21
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wildlifecompliance', '0297_auto_20190906_1438'),
    ]

    operations = [
        migrations.CreateModel(
            name='AllegedCommittedOffence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('included', models.BooleanField(default=True)),
                ('reason_for_removal', models.TextField(blank=True)),
                ('removed', models.BooleanField(default=False)),
                ('alleged_offence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wildlifecompliance.AllegedOffence')),
                ('removed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='alleged_committed_offence_removed_by', to=settings.AUTH_USER_MODEL)),
                ('sanction_outcome', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wildlifecompliance.SanctionOutcome')),
            ],
            options={
                'verbose_name': 'CM_AllegedCommittedOffence',
                'verbose_name_plural': 'CM_AllegedCommittedOffences',
            },
        ),
        migrations.AddField(
            model_name='sanctionoutcome',
            name='alleged_committed_offences',
            field=models.ManyToManyField(related_name='sanction_outcome_alleged_committed_offences', through='wildlifecompliance.AllegedCommittedOffence', to='wildlifecompliance.AllegedOffence'),
        ),
    ]
