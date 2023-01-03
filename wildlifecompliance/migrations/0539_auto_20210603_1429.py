# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-06-03 06:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0538_auto_20210524_1005'),
    ]

    operations = [
        migrations.CreateModel(
            name='SectionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_name', models.CharField(max_length=100)),
                ('group_label', models.CharField(max_length=100)),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='section_groups', to='wildlifecompliance.LicencePurposeSection')),
            ],
            options={
                'verbose_name': 'Schema Section Group',
            },
        ),
        migrations.AlterField(
            model_name='masterlistquestion',
            name='answer_type',
            field=models.CharField(choices=[('text', 'Text'), ('radiobuttons', 'Radio button'), ('checkbox', 'Checkbox'), ('number', 'Number'), ('email', 'Email'), ('select', 'Select'), ('multi-select', 'Multi-select'), ('text_area', 'Text area'), ('label', 'Label'), ('declaration', 'Declaration'), ('file', 'File'), ('date', 'Date'), ('group2', 'Group'), ('expander_table', 'Expander Table'), ('species-all', 'Species List')], default='text', max_length=40, verbose_name='Answer Type'),
        ),
        migrations.AlterField(
            model_name='sectionquestion',
            name='tag',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('isRepeatable', 'isRepeatable'), ('isRequired', 'isRequired')], max_length=400, null=True),
        ),
        migrations.AddField(
            model_name='sectionquestion',
            name='section_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='group_questions', to='wildlifecompliance.SectionGroup'),
        ),
    ]