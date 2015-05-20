# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cts.utils
import django.core.validators
from decimal import Decimal
from shipments.db_views import drop_views, add_views


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0010_recreate_views'),
    ]

    operations = [
        migrations.RunPython(drop_views),
        migrations.CreateModel(
            name='PackageItemDBView',
            fields=[
            ],
            options={
                'verbose_name': 'package item',
                'db_table': 'package_items_view',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='packagedbview',
            options={'verbose_name': 'package'},
        ),
        migrations.AlterModelOptions(
            name='shipmentdbview',
            options={'verbose_name': 'shipment'},
        ),
        migrations.AlterField(
            model_name='kit',
            name='description',
            field=models.CharField(default=b'', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='package',
            name='description',
            field=models.CharField(default=b'', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='packageitem',
            name='price_usd',
            field=cts.utils.USDCurrencyField(decimal_places=3, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)], help_text=b'Price of one unit in US dollars', verbose_name=b'Price USD'),
        ),
        migrations.RunPython(add_views),
    ]
