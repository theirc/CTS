# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def no_op(apps, schema_editor):
    pass



def set_scan_shipment(apps, schema_editor):
    PackageScan = apps.get_model('shipments', 'PackageScan')
    Shipment = apps.get_model('shipments', 'Shipment')

    for shipment in Shipment.objects.all():
        PackageScan.objects.filter(shipment=None, package__shipment=shipment).update(shipment=shipment)


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0022_add_scan_shipment'),
    ]

    operations = [
        migrations.RunPython(set_scan_shipment, no_op),
    ]
