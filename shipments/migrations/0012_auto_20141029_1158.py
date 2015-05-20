# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0011_auto_20141023_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='latitude',
            field=models.DecimalField(null=True, max_digits=13, decimal_places=10),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='location',
            name='longitude',
            field=models.DecimalField(null=True, max_digits=13, decimal_places=10),
            preserve_default=True,
        ),
    ]
