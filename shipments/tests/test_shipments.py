from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now
from accounts.utils import bootstrap_permissions

from currency.currencies import quantize_usd
from shipments.models import Package, Shipment, PackageDBView, ShipmentDBView
from shipments.tests.factories import ShipmentFactory, PackageFactory, PackageItemFactory


class ShipmentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        bootstrap_permissions()

    def test_package_price(self):
        shipment = ShipmentFactory()
        package = PackageFactory(shipment=shipment)
        item1 = PackageItemFactory(package=package,
                                   price_usd=Decimal('1.23'),
                                   quantity=2)
        item2 = PackageItemFactory(package=package,
                                   price_usd=Decimal('9.11'),
                                   quantity=3)
        expected_price = quantize_usd(Decimal(item1.quantity * item1.price_usd
                                              + item2.quantity * item2.price_usd))
        pkg = PackageDBView.objects.get(pk=package.pk)
        price = pkg.price_usd
        self.assertEqual(expected_price, price)

    def test_shipment_price(self):
        shipment = ShipmentFactory()
        package1 = PackageFactory(shipment=shipment)
        PackageItemFactory(package=package1,
                           price_usd=Decimal('1.23'),
                           quantity=2)
        PackageItemFactory(package=package1,
                           price_usd=Decimal('9.11'),
                           quantity=3)
        package2 = PackageFactory(shipment=shipment)
        PackageItemFactory(package=package2,
                           price_usd=Decimal('3.14'),
                           quantity=13)
        pkgs = PackageDBView.objects.filter(pk__in=[package1.pk, package2.pk])
        price_sum = sum([pkg.price_usd for pkg in pkgs])
        expected_price = quantize_usd(price_sum)
        ship = ShipmentDBView.objects.get(pk=shipment.pk)
        price = ship.price_usd
        self.assertEqual(expected_price, price)

    def test_finalize(self):
        shipment = ShipmentFactory()
        pkg2 = PackageFactory(shipment=shipment, name='pkg2')
        pkg1 = PackageFactory(shipment=shipment, name='pkg1')
        self.assertEqual(pkg1.status, Shipment.STATUS_IN_PROGRESS)
        shipment.finalize()
        pkg1 = Package.objects.get(pk=pkg1.pk)
        pkg2 = Package.objects.get(pk=pkg2.pk)
        self.assertEqual(pkg1.status, Shipment.STATUS_READY)
        self.assertEqual(pkg2.number_in_shipment, 1)  # in order of creation
        self.assertEqual(pkg1.number_in_shipment, 2)
        shipment = Shipment.objects.get(pk=shipment.pk)
        self.assertEqual(shipment.status, Shipment.STATUS_READY)
        shipment.reopen()
        pkg1 = Package.objects.get(pk=pkg1.pk)
        self.assertEqual(pkg1.status, Shipment.STATUS_IN_PROGRESS)

    def test_has_shipped(self):
        shipment = ShipmentFactory(status=Shipment.STATUS_IN_PROGRESS)
        self.assertFalse(shipment.has_shipped())
        shipment.status = Shipment.STATUS_READY
        self.assertFalse(shipment.has_shipped())
        shipment.status = Shipment.STATUS_PICKED_UP
        shipment.date_picked_up = now()
        self.assertTrue(shipment.has_shipped())
        shipment.status = Shipment.STATUS_IN_TRANSIT
        shipment.date_in_transit = now()
        self.assertTrue(shipment.has_shipped())
        shipment.status = Shipment.STATUS_LOST
        self.assertTrue(shipment.has_shipped())
        shipment.status = Shipment.STATUS_RECEIVED
        self.assertTrue(shipment.has_shipped())


class PackageTest(TestCase):
    def test_status(self):
        """
        Shipment "status" from get_status() is complicated.
        """
        shipment = ShipmentFactory(
            date_expected=now().date() - timedelta(days=2),
        )
        package = PackageFactory.build(
            shipment=shipment,
            status=Shipment.STATUS_IN_PROGRESS,
            date_received=now().date() - timedelta(days=1),
            date_in_transit=now().date(),
            date_picked_up=now().date(),
        )
        # These three are just returned as-is
        for st in (Shipment.STATUS_CANCELED, Shipment.STATUS_LOST,
                   Shipment.STATUS_IN_PROGRESS):
            package.status = st
            self.assertEqual(package.get_status(), st)
        # Any other status is ignored and it looks at the dates
        package.status = -99
        # We have a date received, so shipment is received
        self.assertEqual(package.get_status(), Shipment.STATUS_RECEIVED)
        package.date_received = None
        # No date received, and date_expected is in the past
        self.assertEqual(package.get_status(), Shipment.STATUS_OVERDUE)

        package.shipment.date_expected = now().date() + timedelta(days=1)
        package.shipment.save()
        # No date received, date-expected in future
        self.assertEqual(package.get_status(), Shipment.STATUS_IN_TRANSIT)
        package.date_in_transit = None
        # Not in transit yet
        self.assertEqual(package.get_status(), Shipment.STATUS_PICKED_UP)
        package.date_picked_up = None
        # Not picked up yet (no idea what the difference is)
        self.assertEqual(package.get_status(), Shipment.STATUS_READY)
