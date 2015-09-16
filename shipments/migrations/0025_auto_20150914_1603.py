# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0024_recreate_views'),
    ]

    operations = [
        migrations.AlterField(
            model_name='packagescan',
            name='shipment',
            field=models.ForeignKey(related_name='scans', to='shipments.Shipment'),
            preserve_default=True,
        ),
    ]
