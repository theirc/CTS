# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0002_add_views'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='status_label',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
    ]
