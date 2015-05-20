# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cts.utils
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_auto_20140925_0813'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalogitem',
            name='price_usd',
            field=cts.utils.USDCurrencyField(decimal_places=3, default=Decimal('0.00'), validators=[django.core.validators.MinValueValidator(0.0)], max_digits=10, blank=True, null=True, verbose_name='Price USD'),
        ),
    ]
