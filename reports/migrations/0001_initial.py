# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.core.validators


def do_nothing(apps, schemaeditor):
    pass


def update_all_donor_shipments(apps, schema_editor):
    PackageItem = apps.get_model("shipments", "PackageItem")
    Donor = apps.get_model("catalog", 'Donor')
    Shipment = apps.get_model('shipments', 'Shipment')
    DonorShipmentData = apps.get_model("reports", "DonorShipmentData")

    # Delete all existing items.
    DonorShipmentData.objects.all().delete()

    for donor in list(Donor.objects.all()) + [None]:
        for shipment in Shipment.objects.all():
            items = PackageItem.objects.filter(donor=donor, package__shipment=shipment)
            num_shipment_items = PackageItem.objects.filter(package__shipment=shipment).count()
            if num_shipment_items:
                percentage_of_shipment = float(len(items)) / num_shipment_items
            else:
                percentage_of_shipment = 0.0
            DonorShipmentData.objects.create(
                donor=donor,
                shipment=shipment,
                item_count=len(items),
                package_count=len(set(i.package_id for i in items)),
                percentage_of_shipment=percentage_of_shipment,
                price_local=sum(i.quantity * i.price_local for i in items),
                price_usd=sum(i.quantity * i.price_usd for i in items),
            )


def update_all_donor_categories(apps, schema_editor):
    PackageItem = apps.get_model("shipments", "PackageItem")
    Donor = apps.get_model("catalog", 'Donor')
    ItemCategory = apps.get_model('catalog', 'ItemCategory')
    DonorCategoryData = apps.get_model("reports", "DonorCategoryData")

    # Delete all existing items.
    DonorCategoryData.objects.all().delete()

    for donor in list(Donor.objects.all()) + [None]:
        for category in ItemCategory.objects.all():
            items = PackageItem.objects.filter(donor=donor, item_category=category)
            if not items:
                DonorCategoryData.objects.filter(donor=donor, category=category).delete()
            else:
                data, _ = DonorCategoryData.objects.get_or_create(donor=donor, category=category)
                data.item_count = len(items)
                data.total_quantity = sum(i.quantity for i in items)
                data.price_local = sum(i.quantity * i.price_local for i in items)
                data.price_usd = sum(i.quantity * i.price_usd for i in items)
                data.save()


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_auto_20140925_0813'),
        ('shipments', '0008_auto_20141001_1506'),
    ]

    operations = [
        migrations.CreateModel(
            name='DonorCategoryData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('item_count', models.PositiveIntegerField(default=0, help_text=b'Number of PackageItems in this Category that were given by this Donor.')),
                ('total_quantity', models.PositiveIntegerField(default=0, help_text=b'Total quantity of PackageItems in this Category that were given by this Donor.')),
                ('price_local', models.DecimalField(default=Decimal('0.0000'), help_text=b'Total extended local price of all items given by this Donor in this Category.', verbose_name=b'Total Price (Local)', max_digits=16, decimal_places=4)),
                ('price_usd', models.DecimalField(default=Decimal('0.00'), help_text=b'Total extended US price of all items given by this Donor in this Category.', verbose_name=b'Total Price (USD)', max_digits=16, decimal_places=2)),
                ('category', models.ForeignKey(blank=True, to='catalog.ItemCategory', null=True)),
                ('donor', models.ForeignKey(blank=True, to='catalog.Donor', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DonorShipmentData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('package_count', models.PositiveIntegerField(default=0, help_text=b'Number of Packages in the Shipment containing at least one PackageItem that was given by this donor.')),
                ('item_count', models.PositiveIntegerField(default=0, help_text=b'Number of PackageItems in this Shipment that were given by this donor.')),
                ('percentage_of_shipment', models.DecimalField(default=Decimal('0.00'), help_text=b'Percent of PackageItems in this Shipment that were given by this donor.', max_digits=5, decimal_places=4)),
                ('price_local', models.DecimalField(decimal_places=4, default=Decimal('0.0000'), max_digits=16, validators=[django.core.validators.MinValueValidator(0.0)], help_text=b'Total extended local price of all items given by this Donor in this Shipment.', verbose_name=b'Total Price (Local)')),
                ('price_usd', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=16, validators=[django.core.validators.MinValueValidator(0.0)], help_text=b'Total extended US price of all items given by this Donor in this Shipment.', verbose_name=b'Total Price (USD)')),
                ('donor', models.ForeignKey(blank=True, to='catalog.Donor', null=True)),
                ('shipment', models.ForeignKey(to='shipments.Shipment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='donorshipmentdata',
            unique_together=set([('donor', 'shipment')]),
        ),
        migrations.AlterUniqueTogether(
            name='donorcategorydata',
            unique_together=set([('donor', 'category')]),
        ),
        migrations.RunPython(update_all_donor_shipments, do_nothing),
        migrations.RunPython(update_all_donor_categories, do_nothing),
    ]
