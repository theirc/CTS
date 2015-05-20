# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.core.validators
import cts.utils


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_auto_20141105_1157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalogitem',
            name='price_local',
            field=models.DecimalField(default=Decimal('0.00'), verbose_name='Price in local currency', max_digits=10, decimal_places=4, validators=[django.core.validators.MinValueValidator(0.0)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='catalogitem',
            name='price_usd',
            field=cts.utils.USDCurrencyField(default=Decimal('0.00'), verbose_name='Price USD', max_digits=10, decimal_places=3, validators=[django.core.validators.MinValueValidator(0.0)]),
            preserve_default=True,
        ),
    ]
