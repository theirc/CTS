from django.test import TestCase
from django.utils.timezone import now

from catalog.tests.factories import CatalogItemFactory

from shipments.models import PackageItem, Shipment, ShipmentDBView, status_as_string
from shipments.tests.factories import PackageFactory, ShipmentFactory, KitItemFactory


class TestPackageItem(TestCase):
    model = PackageItem

    def setUp(self):
        super(TestPackageItem, self).setUp()
        self.package = PackageFactory()
        self.catalog_item = CatalogItemFactory()
        self.quantity = 5

    def _compare(self, package_item, package, catalog_item, quantity):
        self.assertEqual(package_item.package, package)
        self.assertEqual(package_item.catalog_item, catalog_item)
        self.assertEqual(package_item.quantity, quantity)

        self.assertEqual(package_item.description, catalog_item.description)
        self.assertEqual(package_item.unit, catalog_item.unit)
        self.assertEqual(package_item.price_usd, catalog_item.price_usd)
        self.assertEqual(package_item.price_local, catalog_item.price_local)
        self.assertEqual(package_item.item_category, catalog_item.item_category)
        self.assertEqual(package_item.donor, catalog_item.donor)
        self.assertEqual(package_item.donor_t1, catalog_item.donor_t1)
        self.assertEqual(package_item.supplier, catalog_item.supplier)
        self.assertEqual(package_item.weight, catalog_item.weight)

    def test_from_catalog_item(self):
        item = PackageItem.from_catalog_item(
            self.package, self.catalog_item, self.quantity)
        self._compare(item, self.package, self.catalog_item, self.quantity)

    def test_from_kit_item_default_prices(self):
        catalog_item = CatalogItemFactory()
        kit_item = KitItemFactory(catalog_item=catalog_item)
        package = PackageFactory()
        PackageItem.from_kit_item(package, kit_item)


class TestShipment(TestCase):
    model = Shipment

    def setUp(self):
        super(TestShipment, self).setUp()
        self.shipment = ShipmentFactory()

    def test_set_date_in_transit(self):
        self.assertIsNone(self.shipment.date_in_transit)
        self.shipment.status = Shipment.STATUS_IN_TRANSIT
        self.shipment.save()
        shipment = Shipment.objects.get(pk=self.shipment.pk)
        self.assertEqual(now().date(), shipment.date_in_transit)

    def test_set_date_picked_up(self):
        self.assertIsNone(self.shipment.date_picked_up)
        self.shipment.status = Shipment.STATUS_PICKED_UP
        self.shipment.save()
        shipment = Shipment.objects.get(pk=self.shipment.pk)
        self.assertEqual(now().date(), shipment.date_picked_up)


class TestShipmentVerboseStatus(TestCase):
    def test_combinations(self):
        # Test that shipment.verbose_status returns the expected strings

        # Shortcut names for statuses
        PROG = Shipment.STATUS_IN_PROGRESS
        READ = Shipment.STATUS_READY
        TRAN = Shipment.STATUS_IN_TRANSIT
        RCVD = Shipment.STATUS_RECEIVED
        ODUE = Shipment.STATUS_OVERDUE

        # test data is a 3-tuple:
        # * shipment status
        # * list of package statuses, one per package for that shipment (can be empty)
        # * expected status string.

        test_data = [
            (PROG, [], "In progress"),
            (PROG, [PROG], "In progress"),
            # This next one can't happen - setting pkg status sets shipment status ahead
            # (PROG, [TRAN], "In progress"),
            (READ, [], "Ready for pickup"),
            (READ, [PROG], "Ready for pickup"),
            (READ, [READ], "Ready for pickup"),
            (TRAN, [], "In transit"),
            (TRAN, [TRAN, PROG], "In transit (50%)"),
            (TRAN, [TRAN, TRAN], "In transit"),
            (TRAN, [TRAN, RCVD], "In transit (50%)"),
            (RCVD, [], "Received"),
            (RCVD, [TRAN, RCVD], "Received (50%)"),
            (RCVD, [RCVD, RCVD], "Received"),
            (ODUE, [], "Overdue"),
        ]

        # We'll run all the tests without stopping, but set `failed` if any fail
        # and then fail the test at the end.  That'll give us more fine-grained
        # results without having to write N separate tests.
        failed = False
        for shipment_status, package_statuses, expected_status in test_data:
            shipment = ShipmentFactory(status=shipment_status)
            for pkg_status in package_statuses:
                PackageFactory(shipment=shipment, status=pkg_status)
            shipment_from_view = ShipmentDBView.objects.get(pk=shipment.pk)
            shipment_status_str = status_as_string(shipment_status)
            got_status = shipment_from_view.get_verbose_status()
            package_statuses = ','.join([status_as_string(stat) for stat in package_statuses])
            errmsg = "Test failed: with shipment status %s and package statuses %s, expected %s " \
                     "but got %s" % (shipment_status_str, package_statuses, expected_status,
                                     got_status)
            if not expected_status == got_status:
                failed = True
                print(errmsg)
            shipment.packages.all().delete()
            shipment.delete()
        if failed:
            self.fail("Test failed; see previous messages for details")
