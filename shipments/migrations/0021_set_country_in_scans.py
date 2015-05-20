# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def no_op(apps, schema_editor):
    pass


def set_country(apps, schema_editor):
    PackageScan = apps.get_model('shipments', 'PackageScan')
    WorldBorder = apps.get_model('shipments', 'WorldBorder')
    can_update = PackageScan.objects.filter(country=None).exclude(longitude=None).exclude(latitude=None)
    for scan in can_update:
        point = 'POINT (%s %s )' % (scan.longitude, scan.latitude)
        qs = WorldBorder.objects.filter(mpoly__contains=point)
        if qs:
            scan.country = qs[0]
            scan.save()


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0020_dedupe_scans_3'),
    ]

    operations = [
        migrations.RunPython(set_country, no_op),
    ]
