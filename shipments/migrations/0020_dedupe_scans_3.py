# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from shipments.db_views import add_views, drop_views


def no_op(apps, schema_editor):
    pass


def set_last_scan(apps, schema_editor):
    PackageScan = apps.get_model('shipments', 'PackageScan')
    Package = apps.get_model('shipments', 'Package')
    for pkg in Package.objects.filter(last_scan=None):
        pkg.last_scan = PackageScan.objects.filter(package=pkg).order_by('-when').first()
        if pkg.last_scan:
            pkg.last_scan_status_label = pkg.last_scan.status_label
            pkg.save()


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0019_dedupe_scans_2'),
    ]

    operations = [
        migrations.RunPython(
            set_last_scan,
            no_op
        ),
        migrations.RunPython(add_views, drop_views),
        # Add a partial index to keep our scans unique
        migrations.RunSQL(
            '''CREATE UNIQUE INDEX unique_scans ON shipments_location ("package_id", "when")''',
            '''DROP INDEX IF EXISTS unique_scans'''
        )
    ]
