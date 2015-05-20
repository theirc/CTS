# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0005_recreate_views'),
    ]

    operations = [
        migrations.AlterField(
            model_name='packageitem',
            name='price_local',
            field=models.DecimalField(decimal_places=4, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)], help_text=b'Price of one unit in local currency', verbose_name=b'Price in local currency'),
        ),
    ]
