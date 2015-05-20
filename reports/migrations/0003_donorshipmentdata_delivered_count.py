# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def do_nothing(apps, schemaeditor):
    pass

def update_all_donor_shipments(apps, schema_editor):
    PackageItem = apps.get_model("shipments", "PackageItem")
    Donor = apps.get_model("catalog", 'Donor')
    DonorShipmentData = apps.get_model("reports", "DonorShipmentData")
    Shipment = apps.get_model('shipments', 'Shipment')
    # Accessing Shipment this way does not return an object that has access to the STATUS_* attrs
    from shipments.models import Shipment as ShipmentStatusAccessor
    # Delete all existing items.
    DonorShipmentData.objects.all().delete()

    for shipment in Shipment.objects.all():
        all_shipment_items = PackageItem.objects.filter(package__shipment=shipment)
        shipment_items_count = all_shipment_items.count()
        for donor in list(Donor.objects.all()) + [None]:
            items = all_shipment_items.filter(donor=donor)
            item_count = items.count()
            if shipment_items_count:
                percentage = float(item_count)/shipment_items_count
            else:
                percentage = 0.0
            DonorShipmentData.objects.create(
                donor=donor,
                shipment=shipment,
                item_count=item_count,
                delivered_count=items.filter(
                    package__status=ShipmentStatusAccessor.STATUS_RECEIVED
                ).count(),
                package_count=len(set(i.package_id for i in items)),
                percentage_of_shipment=percentage,
                price_local=sum(i.quantity * i.price_local for i in items),
                price_usd=sum(i.quantity * i.price_usd for i in items),
            )

class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_auto_20141014_1117'),
    ]

    operations = [
        migrations.AddField(
            model_name='donorshipmentdata',
            name='delivered_count',
            field=models.PositiveIntegerField(default=0, help_text=b'Number of PackageItems in this Shipment that were given by this donor and whose parent package was  delivered.'),
            preserve_default=True,
        ),
        migrations.RunPython(update_all_donor_shipments, do_nothing),
    ]
