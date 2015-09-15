# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0021_set_country_in_scans'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='packagedbview',
            options={'managed': False, 'verbose_name': 'package'},
        ),
        migrations.AlterModelOptions(
            name='shipmentdbview',
            options={'managed': False, 'verbose_name': 'shipment'},
        ),
        migrations.AlterField(
            model_name='shipment',
            name='status',
            field=models.IntegerField(default=1, db_index=True, choices=[(1, b'In progress'), (2, b'Ready for pickup'), (3, b'Picked up'), (4, b'In transit'), (5, b'Received'), (6, b'Overdue'), (7, b'Lost'), (8, b'Canceled')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='packagescan',
            name='shipment',
            field=models.ForeignKey(related_name='scans', to='shipments.Shipment', null=True),
            preserve_default=True,
        ),
    ]
