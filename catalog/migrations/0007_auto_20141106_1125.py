# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0006_auto_20141105_1158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalogitem',
            name='weight',
            field=models.FloatField(default=0.0, null=True, blank=True, validators=[django.core.validators.MinValueValidator(0.0)]),
            preserve_default=True,
        ),
    ]
