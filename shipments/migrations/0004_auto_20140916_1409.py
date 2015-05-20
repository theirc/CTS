# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0003_auto_20140916_1333'),
    ]

    operations = [
        migrations.AddField(
            model_name='package',
            name='last_location_status_label',
            field=models.CharField(max_length=128, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shipment',
            name='last_location_status_label',
            field=models.CharField(max_length=128, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='location',
            name='status_label',
            field=models.CharField(max_length=128, null=True, blank=True),
        ),
    ]
