# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from decimal import Decimal

from django.db import models, migrations


def no_op(apps, schema_editor):
    pass


def set_null_prices(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    CatalogItem = apps.get_model("catalog", "CatalogItem")
    CatalogItem.objects.filter(price_usd=None).update(price_usd=Decimal('0.000'))
    CatalogItem.objects.filter(price_local=None).update(price_usd=Decimal('0.000'))


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_auto_20141023_1542'),
    ]

    operations = [
        migrations.RunPython(set_null_prices, no_op),
    ]
