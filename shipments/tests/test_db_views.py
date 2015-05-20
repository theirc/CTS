from decimal import Decimal

from django.test import TestCase
from django.utils.timezone import now

from shipments.models import PackageItemDBView, PackageDBView, ShipmentDBView, Shipment
from shipments.tests.factories import PackageItemFactory, PackageFactory, ShipmentFactory


class TestPackageItemsView(TestCase):
    def test_prices(self):
        item = PackageItemFactory(quantity=2, price_usd=Decimal("3.0"), price_local=Decimal("4.0"))
        item = PackageItemDBView.objects.get(pk=item.pk)
        self.assertEqual(Decimal("6.0"), item.extended_price_usd)
        self.assertEqual(Decimal("8.0"), item.extended_price_local)


class TestPackagesView(TestCase):
    def test_prices_and_num_items(self):
        pkg = PackageFactory()
        PackageItemFactory(package=pkg,
                           quantity=2, price_usd=Decimal("3.0"), price_local=Decimal("4.0"))
        PackageItemFactory(package=pkg,
                           quantity=3, price_usd=Decimal("1.0"), price_local=Decimal("0.3"))
        pkg = PackageDBView.objects.get(pk=pkg.pk)
        self.assertEqual(Decimal("9.0"), pkg.price_usd)
        self.assertEqual(Decimal("8.9"), pkg.price_local)
        self.assertEqual(5, pkg.num_items)


class TestShipmentDBView(TestCase):
    # model = ShipmentDBView

    def setUp(self):
        super(TestShipmentDBView, self).setUp()
        self.shipment = ShipmentFactory()

    def test_shipment_db_view_no_packages(self):
        shipment = ShipmentDBView.objects.get(pk=self.shipment.pk)
        self.assertEqual(shipment.description, self.shipment.description)
        # No packages
        self.assertEqual(0, shipment.num_packages)
        self.assertEqual(0, shipment.num_items)
        self.assertEqual(0, shipment.num_received_items)
        self.assertEqual(Decimal('0'), shipment.price_usd)
        self.assertEqual(Decimal('0'), shipment.price_local)

    def test_shipment_db_view_one_package_no_items(self):
        # 1 package, no items
        PackageFactory(shipment=self.shipment)
        shipment = ShipmentDBView.objects.get(pk=self.shipment.pk)
        self.assertEqual(1, shipment.packages.count())
        self.assertEqual(1, shipment.num_packages)
        self.assertEqual(0, shipment.num_items)
        self.assertEqual(0, shipment.num_received_items)
        self.assertEqual(Decimal('0'), shipment.price_usd)
        self.assertEqual(Decimal('0'), shipment.price_local)

    def test_shipment_db_view_one_package_with_items(self):
        # 1 package, with items
        package = PackageFactory(shipment=self.shipment)
        PackageItemFactory(package=package, quantity=1,
                           price_usd=Decimal('1.00'), price_local=Decimal('0.001'))
        PackageItemFactory(package=package, quantity=2,
                           price_usd=Decimal('2.00'), price_local=Decimal('0.002'))
        shipment = ShipmentDBView.objects.get(pk=self.shipment.pk)
        self.assertEqual(1, shipment.packages.count())
        self.assertEqual(1, shipment.num_packages)
        self.assertEqual(3, shipment.num_items)
        self.assertEqual(0, shipment.num_received_items)
        self.assertEqual(Decimal('5.0'), shipment.price_usd)
        self.assertEqual(Decimal('0.005'), shipment.price_local)

    def test_shipment_db_view_two_packages_no_items(self):
        # 2 packages, no items
        PackageFactory(shipment=self.shipment)
        PackageFactory(shipment=self.shipment)
        shipment = ShipmentDBView.objects.get(pk=self.shipment.pk)
        self.assertEqual(2, shipment.packages.count())
        self.assertEqual(2, shipment.num_packages)
        self.assertEqual(0, shipment.num_items)
        self.assertEqual(0, shipment.num_received_items)
        self.assertEqual(Decimal('0'), shipment.price_usd)
        self.assertEqual(Decimal('0'), shipment.price_local)

    def test_shipment_db_view_two_packages_with_items(self):
        # 2 packages, with items, one of them received
        self.shipment.date_received = now()
        self.shipment.status = Shipment.STATUS_RECEIVED
        self.shipment.save()
        package1 = PackageFactory(shipment=self.shipment)
        package2 = PackageFactory(shipment=self.shipment, status=Shipment.STATUS_RECEIVED)
        PackageItemFactory(package=package1, quantity=1,
                           price_usd=Decimal('1.00'), price_local=Decimal('0.001'))
        PackageItemFactory(package=package2, quantity=2,
                           price_usd=Decimal('2.00'), price_local=Decimal('0.002'))
        PackageItemFactory(package=package2, quantity=3,
                           price_usd=Decimal('3.00'), price_local=Decimal('0.003'))
        shipment = ShipmentDBView.objects.get(pk=self.shipment.pk)
        self.assertEqual(2, shipment.packages.count())
        self.assertEqual(2, shipment.num_packages)
        self.assertEqual(6, shipment.num_items)
        self.assertEqual(5, shipment.num_received_items)
        self.assertEqual(Decimal('14.0'), shipment.price_usd)
        self.assertEqual(Decimal('0.014'), shipment.price_local)

    def test_verbose_status_received_percentage(self):
        self.shipment.date_received = now()
        self.shipment.status = Shipment.STATUS_RECEIVED
        self.shipment.save()
        self.assertEqual(self.shipment.status, Shipment.STATUS_RECEIVED)
        shipment = ShipmentDBView.objects.get(pk=self.shipment.pk)
        # No packages: should not show any percent (they're all "received")
        self.assertEqual(0, shipment.num_packages)
        self.assertEqual('Received', shipment.get_verbose_status())
        # Add one, unreceived package
        PackageFactory(shipment=self.shipment, status=Shipment.STATUS_IN_TRANSIT)
        shipment = ShipmentDBView.objects.get(pk=self.shipment.pk)
        # Should still show 0%
        self.assertEqual(1, shipment.num_packages)
        self.assertEqual('Received (0%)', shipment.get_verbose_status())
        # Add a second package, this one received
        PackageFactory(shipment=self.shipment, status=Shipment.STATUS_RECEIVED)
        shipment = ShipmentDBView.objects.get(pk=self.shipment.pk)
        # Now should show 50%
        self.assertEqual(2, shipment.num_packages)
        self.assertEqual('Received (50%)', shipment.get_verbose_status())
        # Set all packages to received
        self.shipment.packages.update(status=Shipment.STATUS_RECEIVED)
        shipment = ShipmentDBView.objects.get(pk=self.shipment.pk)
        # Now should show no percentage, just the status
        self.assertEqual(2, shipment.num_packages)
        self.assertEqual('Received', shipment.get_verbose_status())
