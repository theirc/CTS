from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from accounts.models import ROLE_PARTNER
from accounts.tests.factories import CtsUserFactory
from catalog.tests.factories import CatalogItemFactory
from shipments.forms import ShipmentEditForm, PackageEditForm, PackageItemCreateForm
from shipments.models import Shipment, PackageItem
from shipments.tests.factories import ShipmentFactory, PackageFactory


class BaseFormTestCase(TestCase):
    def setUp(self):
        self.description = 'Yet Another _shipment_ DESCRIPTION'
        self.partner = CtsUserFactory(role=ROLE_PARTNER, name='Some Partner')


class ShipmentEditFormTestCase(BaseFormTestCase):
    def test_create_good(self):
        shipment_date = (timezone.now() + timedelta(days=2)).date()
        data = {
            'description': self.description,
            'shipment_date': shipment_date,
            'estimated_delivery': 0,
            'partner': self.partner.id,
            'store_release': 'foo'
        }
        form = ShipmentEditForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        shipment = form.save()
        self.assertEqual(Shipment.objects.get(pk=shipment.pk).description, data['description'])
        shipment = Shipment.objects.get(pk=shipment.pk)
        self.assertEqual(shipment_date, shipment.date_expected)

    def test_create_bad(self):
        data = {
            'description': self.description,
        }
        form = ShipmentEditForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('estimated_delivery', form.errors.keys())

    def test_create_but_use_default_description(self):
        shipment_date = (timezone.now() + timedelta(days=2)).date()
        print("Shipment date = %s" % shipment_date)
        store_release = '123'
        data = {
            'description': '',
            'shipment_date': shipment_date.strftime('%Y-%m-%d'),
            'estimated_delivery': 0,
            'store_release': store_release,
            'partner': self.partner.id
        }
        form = ShipmentEditForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        print("cleaned_data = %s" % form.cleaned_data)
        shipment = form.save()
        print("shipment.shipment_date = %s" % shipment.shipment_date)
        shipment_date = datetime.strftime(shipment_date, "%Y-%m-%d")
        description = '-'.join([self.partner.name, store_release, shipment_date])
        self.assertEqual('', Shipment.objects.get(pk=shipment.pk).description)
        self.assertEqual(shipment_date, shipment.shipment_date)
        self.assertEqual(shipment_date, Shipment.objects.get(pk=shipment.pk).shipment_date)
        self.assertEqual(Shipment.objects.get(pk=shipment.pk).__unicode__(), description)

    def test_edit(self):
        shipment_date = (timezone.now() + timedelta(days=2)).date()
        shipment = ShipmentFactory(
            description='First',
            shipment_date=shipment_date,
            date_expected=shipment_date + timedelta(days=3),
        )
        data = {
            'description': 'New description',
            'shipment_date': shipment_date,
            'estimated_delivery': 1,
            'store_release': 'foo',
            'partner': self.partner.id
        }
        form = ShipmentEditForm(instance=shipment, data=data)
        self.assertTrue(form.is_valid())
        result = form.save()
        self.assertEqual(shipment.pk, result.pk)
        self.assertEqual('New description', result.description)
        self.assertEqual(shipment_date + timedelta(days=1),
                         result.date_expected)

    def test_create_exceeds_estimated_delivery_min_max(self):
        shipment_date = (timezone.now() + timedelta(days=2)).date()
        data = {
            'description': self.description,
            'shipment_date': shipment_date,
            'estimated_delivery': 1000,
        }
        form = ShipmentEditForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('estimated_delivery', form.errors.keys())
        data['estimated_delivery'] = -1
        form = ShipmentEditForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('estimated_delivery', form.errors.keys())


class PackageEditFormTestCase(TestCase):
    def test_pkg_edit_no_shipment(self):
        # Provide a package to edit that has a shipment
        package = PackageFactory()
        data = {
            'name': package.name,
            'description': 'New description',
        }
        form = PackageEditForm(instance=package, data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        pkg = form.save()
        self.assertEqual(data['description'], pkg.description)

    def test_pkg_edit_specify_shipment(self):
        # Creating a new instance, specify shipment
        shipment = ShipmentFactory()
        data = {
            'name': 'New name',
            'description': 'New description',
        }
        form = PackageEditForm(data=data, shipment=shipment)
        pkg = form.save()
        self.assertEqual(shipment, pkg.shipment)
        self.assertEqual(data['name'], pkg.name)
        self.assertEqual(data['description'], pkg.description)


class TestPackageItemCreateForm(TestCase):
    form_class = PackageItemCreateForm

    def setUp(self):
        super(TestPackageItemCreateForm, self).setUp()
        self.package = PackageFactory()
        self.catalog_item = CatalogItemFactory()
        self.data = {
            'catalog_item_0': self.catalog_item.description,
            'catalog_item_1': self.catalog_item.pk,
            'quantity': 3,
        }

    def get_form(self):
        return self.form_class(package=self.package, data=self.data)

    def test_catalog_item_required(self):
        """Catalog item specification is required."""
        self.data.pop('catalog_item_1')
        form = self.get_form()
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('catalog_item' in form.errors)
        self.assertEqual(PackageItem.objects.count(), 0)

    def test_catalog_item_invalid(self):
        """Catalog item must refer to a valid object."""
        self.data['catalog_item_1'] = 'invalid'
        form = self.get_form()
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('catalog_item' in form.errors)
        self.assertEqual(PackageItem.objects.count(), 0)

    def test_quantity_required(self):
        """Quantity is required."""
        self.data.pop('quantity')
        form = self.get_form()
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('quantity' in form.errors)
        self.assertEqual(PackageItem.objects.count(), 0)

    def test_quantity_invalid(self):
        """Quantity must be an integer."""
        self.data['quantity'] = 'invalid'
        form = self.get_form()
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('quantity' in form.errors)
        self.assertEqual(PackageItem.objects.count(), 0)

    def test_quantity_zero(self):
        """Quantity must not be 0."""
        self.data['quantity'] = 0
        form = self.get_form()
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('quantity' in form.errors)
        self.assertEqual(PackageItem.objects.count(), 0)

    def test_quantity_negative(self):
        """Quantity must not be negative."""
        self.data['quantity'] = -5
        form = self.get_form()
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('quantity' in form.errors)
        self.assertEqual(PackageItem.objects.count(), 0)

    def test_valid(self):
        """
        Saving a valid form should create a PackageItem with correct values.
        """
        form = self.get_form()
        self.assertTrue(form.is_valid())
        item = form.save()
        self.assertEqual(item.package, self.package)
        self.assertEqual(item.quantity, self.data['quantity'])
        self.assertEqual(item.catalog_item, self.catalog_item)
        self.assertEqual(PackageItem.objects.count(), 1)
