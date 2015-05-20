# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0015_auto_20141030_1225'),
    ]

    operations = [
        migrations.AlterField(
            model_name='packageitem',
            name='weight',
            field=models.FloatField(default=0.0, help_text=b'Weight of one unit', null=True, blank=True, validators=[django.core.validators.MinValueValidator(0.0)]),
            preserve_default=True,
        ),
    ]
