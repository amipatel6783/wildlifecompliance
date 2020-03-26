# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-06-19 09:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0180_auto_20190605_1309'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReturnInvoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_reference', models.CharField(blank=True, default='', max_length=50, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='return',
            name='return_fee',
            field=models.DecimalField(decimal_places=2, default='0', max_digits=8),
        ),
        migrations.AddField(
            model_name='returninvoice',
            name='invoice_return',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='wildlifecompliance.Return'),
        ),
    ]