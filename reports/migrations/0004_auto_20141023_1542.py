# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cts.utils
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_donorshipmentdata_delivered_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donorcategorydata',
            name='price_usd',
            field=cts.utils.USDCurrencyField(decimal_places=3, default=Decimal('0.00'), max_digits=16, validators=[django.core.validators.MinValueValidator(0.0)], help_text=b'Total extended US price of all items given by this Donor in this Category.', verbose_name=b'Total Price (USD)'),
        ),
        migrations.AlterField(
            model_name='donorshipmentdata',
            name='price_usd',
            field=cts.utils.USDCurrencyField(decimal_places=3, default=Decimal('0.00'), max_digits=16, validators=[django.core.validators.MinValueValidator(0.0)], help_text=b'Total extended US price of all items given by this Donor in this Shipment.', verbose_name=b'Total Price (USD)'),
        ),
    ]
