# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from shipments.db_views import drop_views, add_views


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0013_merge'),
    ]

    operations = [
        migrations.RunPython(drop_views, add_views),
        migrations.RenameModel("Location", "PackageScan"),
        migrations.AlterModelTable(
            name='packagescan',
            table='shipments_location',
        ),
        migrations.RenameField(
            model_name='package',
            old_name='last_location',
            new_name='last_scan',
        ),
        migrations.RenameField(
            model_name='package',
            old_name='last_location_status_label',
            new_name='last_scan_status_label',
        ),
        migrations.RenameField(
            model_name='shipment',
            old_name='last_location_status_label',
            new_name='last_scan_status_label',
        ),
        migrations.RunPython(add_views, drop_views),
    ]
