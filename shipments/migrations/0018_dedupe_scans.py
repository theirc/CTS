# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from shipments.db_views import drop_views, add_views


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0017_merge'),
    ]

    operations = [
        migrations.RunPython(drop_views, add_views),
        migrations.RemoveField(
            model_name='package',
            name='last_scan',
        ),
        migrations.RemoveField(
            model_name='package',
            name='last_scan_status_label',
        ),
        migrations.AlterField(
            model_name='packagescan',
            name='when',
            field=models.DateTimeField(db_index=True),
            preserve_default=True,
        ),
    ]
