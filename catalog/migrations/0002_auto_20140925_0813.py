# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalogitem',
            name='price_local',
            field=models.DecimalField(decimal_places=4, default=Decimal('0.00'), validators=[django.core.validators.MinValueValidator(0.0)], max_digits=10, blank=True, null=True, verbose_name='Price in local currency'),
        ),
    ]
