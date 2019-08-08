# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-06 00:41
from __future__ import unicode_literals

from django.db import migrations, models
from ledger.payments.models import CashTransaction

def rename_eft(apps, schema_editor):
    CashTransaction = apps.get_model('cash','CashTransaction')
    try:
        for c in CashTransaction.objects.all():
            if c.source == 'eft':
                c.source = 'eftpos'
                c.save()
    except Exception as e:
        raise e


class Migration(migrations.Migration):

    dependencies = [
        ('cash', '0008_auto_20160823_1315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cashtransaction',
            name='source',
            field=models.CharField(choices=[('cash', 'cash'), ('cheque', 'cheque'), ('eftpos', 'eftpos'), ('money_order', 'money_order')], max_length=11),
        ),
        migrations.RunPython(rename_eft),
    ]
