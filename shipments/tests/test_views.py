import json

from PIL import Image
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.encoding import force_text
from accounts.models import ROLE_PARTNER
from accounts.tests.factories import CtsUserFactory
from accounts.utils import bootstrap_permissions

from catalog.tests.factories import CatalogItemFactory, DonorFactory, \
    SupplierFactory
from ona.models import FormSubmission
from ona.representation import PackageScanFormSubmission
from ona.tests.test_models import PACKAGE_DATA, QR_CODE
from shipments.models import Shipment, Package, PackageItem
from shipments.views import ShipmentCreateView
from shipments.tests.factories import ShipmentFactory, PackageFactory, \
    KitFactory, KitItemFactory, PackageItemFactory


class BaseViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        bootstrap_permissions()

    def setUp(self):
        self.email = 'fred@example.com'
        self.password = 'flintstone'
        self.user = get_user_model().objects.create_superuser(password=self.password,
                                                              email=self.email)
        assert self.client.login(email=self.email,
                                 password=self.password)
        self.description = 'Yet Another _shipment_ DESCRIPTION'
        self.shipment = ShipmentFactory(description=self.description, partner=self.user)

    def just_partner(self):
        # Make self.user just a partner
        self.user.is_superuser = False
        self.user.role = ROLE_PARTNER
        self.user.save()
        self.assertTrue(self.user.is_just_partner())

    def assertNoPermission(self, rsp):
        self.assertRedirects(rsp, '/login/?next=' + self.url)

    def assert200(self, rsp):
        self.assertEqual(200, rsp.status_code)

    def assert404(self, rsp):
        self.assertEqual(404, rsp.status_code)


class ShipmentsListViewTest(BaseViewTestCase):
    def test_get(self):
        rsp = self.client.get(reverse('shipments_list'))
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'shipments/list.html')
        self.assertContains(rsp, self.description)


class ShipmentCreateViewTest(BaseViewTestCase):
    def test_get(self):
        rsp = self.client.get(reverse('create_shipment'))
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'shipments/create_edit_shipment.html')

    def test_creating_is_true(self):
        self.assertTrue(ShipmentCreateView().creating())

    def test_post_good(self):
        partner = CtsUserFactory(role=ROLE_PARTNER)
        data = {
            'description': 'DESCRIPTION',
            'shipment_date': force_text(timezone.now().date()),
            'estimated_delivery': 2,
            'partner': partner.id,
            'store_release': 'foo'
        }
        rsp = self.client.post(reverse('create_shipment'), data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        new_shipment = Shipment.objects.exclude(pk=self.shipment.pk).get()
        next_url = reverse('edit_shipment', kwargs={'pk': new_shipment.pk})
        self.assertRedirects(rsp, next_url)
        self.assertEqual('DESCRIPTION', new_shipment.description)

    def test_post_bad(self):
        data = {
            'description': 'DESCRIPTION',
            'shipment_date': 'this is not a date',  # BAD DATA
            'estimated_delivery': 2,
        }
        rsp = self.client.post(reverse('create_shipment'), data=data)
        self.assertEqual(400, rsp.status_code)

    def test_just_partner(self):
        # Partner may not create a shipment
        self.just_partner()
        self.url = reverse('create_shipment')
        rsp = self.client.get(self.url)
        self.assertNoPermission(rsp)


class ShipmentLostViewTest(BaseViewTestCase):
    def setUp(self):
        super(ShipmentLostViewTest, self).setUp()
        self.url = reverse('lost_shipment', args=[self.shipment.pk])

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)

    def test_post(self):
        note = 'My dog ate it'
        data = {
            'acceptable': True,
            'notes': note,
        }
        self.assertNotEqual(self.shipment.status, Shipment.STATUS_LOST)
        rsp = self.client.post(self.url, data)
        new_url = reverse('edit_shipment', args=[self.shipment.pk])
        self.assertRedirects(rsp, new_url)
        self.shipment = Shipment.objects.get(pk=self.shipment.pk)
        self.assertEqual(self.shipment.status, Shipment.STATUS_LOST)
        self.assertEqual(self.shipment.status_note, note)
        self.assertEqual(self.shipment.acceptable, True)


class ShipmentUpdateViewTest(BaseViewTestCase):
    def setUp(self):
        super(ShipmentUpdateViewTest, self).setUp()
        self.url = reverse('edit_shipment', kwargs={'pk': self.shipment.pk})
        self.package = PackageFactory(shipment=self.shipment)

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'shipments/create_edit_shipment.html')
        self.assertContains(rsp, self.description)
        # The context actually has ShipmentDBView and PackageDBView objects, so
        # look for the PKs
        self.assertIn(self.shipment.pk, [s.pk for s in rsp.context['shipments']])
        self.assertIn(self.package.pk, [p.pk for p in rsp.context['packages']])

    def test_post_good(self):
        partner = CtsUserFactory(role=ROLE_PARTNER)
        data = {
            'description': 'DESCRIPTION',
            'shipment_date': force_text(timezone.now().date()),
            'estimated_delivery': 2,
            'partner': partner.id,
            'store_release': 'foo'
        }
        rsp = self.client.post(self.url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertRedirects(rsp, reverse('edit_shipment', args=[self.shipment.pk]))
        shipment = Shipment.objects.get(pk=self.shipment.pk)
        self.assertEqual(data['description'], shipment.description)

    def test_post_bad(self):
        data = {
            'description': 'DESCRIPTION',
            'shipment_date': 'not a VALID date',
            'estimated_delivery': 2,
        }
        rsp = self.client.post(self.url, data=data)
        self.assertEqual(400, rsp.status_code)
        self.assertIn('shipment_date', rsp.context['form'].errors.keys())

    def test_just_partner_get_own(self):
        # Partner may view a shipment if it's theirs
        self.just_partner()
        rsp = self.client.get(self.url)
        self.assert200(rsp)

    def test_just_partner_get_other(self):
        # Partner may not view other partners' shipments
        # Just acts like it's not there (404)
        self.just_partner()
        partner = CtsUserFactory(role=ROLE_PARTNER)
        self.shipment.partner = partner
        self.shipment.save()
        rsp = self.client.get(self.url)
        self.assert404(rsp)

    def test_just_partner_post(self):
        # Partner may not update a shipment
        self.just_partner()
        data = {
            'description': 'DESCRIPTION',
            'shipment_date': force_text(timezone.now().date()),
            'estimated_delivery': 2,
            'partner': self.user.id,
            'store_release': 'foo'
        }
        rsp = self.client.post(self.url, data=data)
        self.assertNoPermission(rsp)


class NewPackageModalViewTest(BaseViewTestCase):
    def setUp(self):
        super(NewPackageModalViewTest, self).setUp()
        self.url = reverse('new_package', kwargs={'pk': self.shipment.pk})

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'shipments/new_package_modal.html')

    def test_post(self):
        data = {
            'name': 'package name',
            'description': 'desscRIPERERtion',
            'package_quantity': '1',
        }
        rsp = self.client.post(self.url, data=data)
        self.assertEqual(200, rsp.status_code)
        pkg = Package.objects.get()
        self.assertEqual(self.shipment, pkg.shipment)
        self.assertEqual(data['name'], pkg.name)

    def test_just_partner(self):
        # Partner may not create a new package
        self.just_partner()
        self.assertFalse(self.user.has_perm('shipments.add_package'))
        rsp = self.client.get(self.url)
        self.assertNoPermission(rsp)


class EditPackageModalViewTest(BaseViewTestCase):
    def setUp(self):
        super(EditPackageModalViewTest, self).setUp()
        self.package = PackageFactory()
        self.url = reverse('edit_package', kwargs={'pk': self.package.pk})

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'shipments/edit_package_modal.html')

    def test_post(self):
        data = {
            'name': 'package name',
            'description': 'desscRIPERERtion',
        }
        rsp = self.client.post(self.url, data=data)
        self.assertEqual(200, rsp.status_code)
        pkg = Package.objects.get()
        self.assertEqual(data['name'], pkg.name)

    def test_just_partner(self):
        # Partner may not edit a package
        self.just_partner()
        self.assertFalse(self.user.has_perm('shipments.change_package'))
        rsp = self.client.get(self.url)
        self.assertNoPermission(rsp)


class ShipmentDeleteViewTest(BaseViewTestCase):
    def setUp(self):
        super(ShipmentDeleteViewTest, self).setUp()
        self.shipment = ShipmentFactory()
        self.package = PackageFactory(shipment=self.shipment)
        self.item = PackageItemFactory(package=self.package)
        self.url = reverse('delete_shipment', kwargs={'pk': self.shipment.pk})

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        Shipment.objects.get(pk=self.shipment.pk)
        PackageItem.objects.get(pk=self.item.pk)

    def test_post(self):
        rsp = self.client.post(self.url)
        self.assertRedirects(rsp, reverse('shipments_list'))
        self.assertFalse(Shipment.objects.filter(pk=self.shipment.pk).exists())
        self.assertFalse(Package.objects.filter(pk=self.package.pk).exists())
        self.assertFalse(PackageItem.objects.filter(pk=self.item.pk).exists())

    def test_just_partner(self):
        # Partner may not delete a shipment
        self.just_partner()
        self.assertFalse(self.user.has_perm('shipments.delete_shipment'))
        rsp = self.client.get(self.url)
        self.assertNoPermission(rsp)


class NewPackageFromKitModalViewTest(BaseViewTestCase):
    def setUp(self):
        super(NewPackageFromKitModalViewTest, self).setUp()
        self.kit = KitFactory()
        self.kit_item = KitItemFactory(kit=self.kit, quantity=3)
        self.url = reverse('new_package_from_kit', kwargs={'pk': self.shipment.pk})

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'shipments/new_package_from_kit_modal.html')

    def test_post_one_kit(self):
        data = {
            'name': 'package name',
            'description': 'desscRIPERERtion',
            'kit-quantity-%d' % self.kit.pk: 3,
            'package_quantity': '1',
        }
        rsp = self.client.post(self.url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(200, rsp.status_code)
        pkg = Package.objects.get()
        self.assertEqual(self.shipment, pkg.shipment)
        self.assertEqual(self.kit, pkg.kit)
        pkg_item = PackageItem.objects.get(package=pkg)
        self.assertEqual(self.kit_item.catalog_item, pkg_item.catalog_item)
        self.assertEqual(self.kit_item.quantity * 3, pkg_item.quantity)

    def test_post_no_kits(self):
        data = {
            'name': 'package name',
            'description': 'desscRIPERERtion',
            'package_quantity': '1',
        }
        rsp = self.client.post(self.url, data=data)
        self.assertEqual(400, rsp.status_code)

    def test_post_two_kits(self):
        kit2 = KitFactory()
        KitItemFactory(kit=kit2)
        data = {
            'name': 'package name',
            'description': 'desscRIPERERtion',
            'kit-quantity-%d' % self.kit.pk: 1,
            'kit-quantity-%d' % kit2.pk: 2,
            'package_quantity': '1',
        }
        rsp = self.client.post(self.url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(200, rsp.status_code)
        pkg = Package.objects.get()
        self.assertEqual(self.shipment, pkg.shipment)
        self.assertIsNone(pkg.kit)
        pkg_items = PackageItem.objects.filter(package=pkg)
        self.assertEqual(2, pkg_items.count())

    def test_post_four_packages(self):
        data = {
            'name': 'package name',
            'description': 'desscRIPERERtion',
            'kit-quantity-%d' % self.kit.pk: 3,
            'package_quantity': '4',
        }
        rsp = self.client.post(self.url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(200, rsp.status_code)
        pkgs = Package.objects.filter(shipment=self.shipment, kit=self.kit)
        self.assertEqual(4, pkgs.count())
        pkg_items = PackageItem.objects.filter(package__in=pkgs,
                                               catalog_item=self.kit_item.catalog_item,
                                               quantity=self.kit_item.quantity * 3)
        self.assertEqual(4, pkg_items.count())

    def test_just_partner(self):
        # Partner may not create a package
        self.just_partner()
        rsp = self.client.get(self.url)
        self.assertNoPermission(rsp)


class PackageItemsViewTestCase(BaseViewTestCase):
    def setUp(self):
        super(PackageItemsViewTestCase, self).setUp()
        self.package = PackageFactory(shipment=self.shipment)
        self.package_items = [
            PackageItemFactory(package=self.package),
            PackageItemFactory(package=self.package),
        ]
        self.url = reverse('package_items', kwargs={'pk': self.package.pk})

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(self.package, rsp.context['package'])
        for item in self.package_items:
            self.assertIn(item, rsp.context['package_items'])
        self.assertTemplateUsed(rsp, 'shipments/package_items.html')

    def test_just_partner(self):
        # Partner may view a shipment's package items, but only if it's the user's shipment
        self.just_partner()
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        self.shipment.partner = CtsUserFactory()
        self.shipment.save()
        rsp = self.client.get(self.url)
        self.assertEqual(404, rsp.status_code)


class PackageDeleteViewTestCase(BaseViewTestCase):
    def setUp(self):
        super(PackageDeleteViewTestCase, self).setUp()
        self.package = PackageFactory(shipment=self.shipment)
        self.package_items = [
            PackageItemFactory(package=self.package),
            PackageItemFactory(package=self.package),
        ]
        self.url = reverse('package_delete', kwargs={'pk': self.package.pk})

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'cts/confirm_delete.html')
        self.assertEqual(self.package, rsp.context['object'])

    def test_post(self):
        rsp = self.client.post(self.url)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertFalse(Package.objects.filter(pk=self.package.pk).exists())
        for item in self.package_items:
            self.assertFalse(PackageItem.objects.filter(pk=item.pk).exists())

    def test_just_partner(self):
        # Partner may not delete a package
        self.just_partner()
        rsp = self.client.get(self.url)
        self.assertNoPermission(rsp)


class PackageItemDeleteViewTestCase(BaseViewTestCase):
    def setUp(self):
        super(PackageItemDeleteViewTestCase, self).setUp()
        self.package = PackageFactory(shipment=self.shipment)
        self.package_items = [
            PackageItemFactory(package=self.package),
            PackageItemFactory(package=self.package),
        ]
        self.item = self.package_items[0]
        self.url = reverse('package_item_delete', kwargs={'pk': self.item.pk})

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'cts/confirm_delete.html')
        self.assertEqual(self.item, rsp.context['object'])
        PackageItem.objects.get(pk=self.item.pk)

    def test_post(self):
        rsp = self.client.post(self.url)

        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertTrue(Package.objects.filter(pk=self.package.pk).exists())
        self.assertFalse(PackageItem.objects.filter(pk=self.item.pk).exists())
        item2 = self.package_items[1]
        self.assertTrue(PackageItem.objects.filter(pk=item2.pk).exists())

    def test_just_partner(self):
        # Partner may not delete a package item
        self.just_partner()
        rsp = self.client.get(self.url)
        self.assertNoPermission(rsp)


class TestPackageItemCreateView(BaseViewTestCase):
    url_name = "package_item_create"

    def setUp(self):
        super(TestPackageItemCreateView, self).setUp()
        self.package = PackageFactory()
        self.catalog_item = CatalogItemFactory()
        self.data = {
            'catalog_item_0': self.catalog_item.description,
            'catalog_item_1': self.catalog_item.pk,
            'quantity': 5,
        }

    def get_url(self, package_id=None):
        if package_id is None:
            package_id = self.package.pk
        return reverse(self.url_name, args=[package_id])

    def test_get_unauthenticated(self):
        """User must be authenticated to create a package item."""
        self.client.logout()
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PackageItem.objects.count(), 0)

    def test_post_unauthenticated(self):
        """User must be authenticated to create a package item."""
        self.client.logout()
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PackageItem.objects.count(), 0)

    def test_invalid_package(self):
        """Package item must be added to a valid package."""
        response = self.client.get(self.get_url('12345'))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(PackageItem.objects.count(), 0)

    def test_get(self):
        """GET should retrieve an unbound form."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(PackageItem.objects.count(), 0)

    def test_post_valid(self):
        """Valid POST should create a new package item."""
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "")
        self.assertEqual(PackageItem.objects.count(), 1)
        item = PackageItem.objects.get()
        self.assertEqual(item.package, self.package)
        self.assertEqual(item.catalog_item, self.catalog_item)
        self.assertEqual(item.quantity, self.data['quantity'])

    def test_post_invalid(self):
        """Invalid POST should return the form with errors."""
        self.data.pop('quantity')
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].is_bound)
        self.assertFalse(response.context['form'].is_valid())
        self.assertTrue('quantity' in response.context['form'].errors)
        self.assertEqual(PackageItem.objects.count(), 0)

    def test_just_partner(self):
        # Partner may not create a package item
        self.just_partner()
        self.url = self.get_url()
        rsp = self.client.get(self.url)
        self.assertNoPermission(rsp)


class PackageItemEditModalViewTest(BaseViewTestCase):
    def setUp(self):
        super(PackageItemEditModalViewTest, self).setUp()
        self.package = PackageFactory(shipment=self.shipment)
        self.item = PackageItemFactory(package=self.package)
        self.url = reverse('package_item_edit', args=[self.item.pk])

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)

    def test_post(self):
        data = model_to_dict(self.item)
        new_description = 'A very good time'
        data['description'] = new_description
        # On success, it just returns an empty 200 response (since it's just a modal)
        rsp = self.client.post(self.url, data)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual('', rsp.content)
        item = PackageItem.objects.get(pk=self.item.pk)
        self.assertEqual(new_description, item.description)


class SummaryManifestViewTest(BaseViewTestCase):
    def test_it(self):
        self.packages = [PackageFactory(shipment=self.shipment) for i in range(5)]
        for pkg in self.packages:
            for i in range(5):
                PackageItemFactory(package=pkg)
        url = reverse('summary_manifests', kwargs={'pk': self.shipment.pk})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Summary manifest doesn't change shipment status
        shipment = Shipment.objects.get(pk=self.shipment.pk)
        self.assertEqual(Shipment.STATUS_IN_PROGRESS, shipment.status)

    def test_just_partner(self):
        # Partner may not view another's shipment
        self.url = reverse('summary_manifests', kwargs={'pk': self.shipment.pk})
        self.just_partner()
        self.shipment.partner = CtsUserFactory()
        self.shipment.save()
        rsp = self.client.get(self.url)
        self.assertEqual(404, rsp.status_code)


class PackageBarcodesViewTest(BaseViewTestCase):
    def test_it(self):
        self.packages = [PackageFactory(shipment=self.shipment) for i in range(5)]
        for pkg in self.packages:
            for i in range(5):
                PackageItemFactory(package=pkg)
        url = reverse('package_barcodes',
                      kwargs={'pk': self.shipment.pk,
                              'size': 16,
                              'labels': '1,2'})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Printing barcodes updates status from inprogress to ready for pickup
        shipment = Shipment.objects.get(pk=self.shipment.pk)
        self.assertEqual(Shipment.STATUS_READY, shipment.status)
        for pkg in self.packages:
            pkg = Package.objects.get(pk=pkg.pk)
            self.assertEqual(Shipment.STATUS_READY, pkg.status)

    def test_just_partner(self):
        # Partner may not view another's shipment
        self.just_partner()
        self.shipment.partner = CtsUserFactory()
        self.shipment.save()
        self.url = reverse('package_barcodes',
                           kwargs={'pk': self.shipment.pk,
                                   'size': 6,
                                   'labels': '3,4'})
        rsp = self.client.get(self.url)
        self.assertEqual(404, rsp.status_code)


class FullManifestViewTest(BaseViewTestCase):
    def test_it(self):
        self.packages = [PackageFactory(shipment=self.shipment) for i in range(5)]
        for pkg in self.packages:
            for i in range(5):
                PackageItemFactory(package=pkg)
        url = reverse('full_manifests',
                      kwargs={'pk': self.shipment.pk,
                              'size': 6})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Printing barcodes updates status from inprogress to ready for pickup
        shipment = Shipment.objects.get(pk=self.shipment.pk)
        self.assertEqual(Shipment.STATUS_READY, shipment.status)
        for pkg in self.packages:
            pkg = Package.objects.get(pk=pkg.pk)
            self.assertEqual(Shipment.STATUS_READY, pkg.status)

    def test_just_partner(self):
        # Partner may not view another's shipment
        self.just_partner()
        self.shipment.partner = CtsUserFactory()
        self.shipment.save()
        self.url = reverse('full_manifests',
                           kwargs={'pk': self.shipment.pk,
                                   'size': 8})
        rsp = self.client.get(self.url)
        self.assertEqual(404, rsp.status_code)


class QRCodeTest(TestCase):
    @classmethod
    def setUpClass(cls):
        bootstrap_permissions()

    def test_qrcode(self):
        code = '12345-234324234'
        url = reverse('qrcode', kwargs={'code': code})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual('image/png', rsp['Content-Type'])
        bits = BytesIO(rsp.content)
        img = Image.open(bits)
        self.assertEqual('PNG', img.format)
        self.assertEqual((84, 84), img.size)

    def test_qrcode_l(self):
        code = '12345-234324234'
        url = reverse('qrcode_l', kwargs={'code': code})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual('image/png', rsp['Content-Type'])
        bits = BytesIO(rsp.content)
        img = Image.open(bits)
        self.assertEqual('PNG', img.format)
        self.assertEqual((210, 210), img.size)

    def test_qrcode_vl(self):
        code = '12345-234324234'
        url = reverse('qrcode_vl', kwargs={'code': code})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual('image/png', rsp['Content-Type'])
        bits = BytesIO(rsp.content)
        img = Image.open(bits)
        self.assertEqual('PNG', img.format)
        self.assertEqual((2100, 2100), img.size)

    def test_qrcode_s(self):
        code = '12345-234324234'
        url = reverse('qrcode_sized', kwargs={'code': code, 'size': 6})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual('image/png', rsp['Content-Type'])
        bits = BytesIO(rsp.content)
        img = Image.open(bits)
        self.assertEqual('PNG', img.format)
        self.assertEqual((84, 84), img.size)

        url = reverse('qrcode_sized', kwargs={'code': code, 'size': 8})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual('image/png', rsp['Content-Type'])
        bits = BytesIO(rsp.content)
        img = Image.open(bits)
        self.assertEqual('PNG', img.format)
        self.assertEqual((210, 210), img.size)


class BulkEditPackageItemsViewTest(BaseViewTestCase):
    def setUp(self):
        super(BulkEditPackageItemsViewTest, self).setUp()
        self.url = reverse('bulk_edit_package_items')

    def test_get(self):
        # Pass package item pks in a header
        # get back a modal with a form
        pkg = PackageFactory(shipment=self.shipment)
        pkg_items = [PackageItemFactory(package=pkg) for i in range(10)]
        items_to_edit = pkg_items[:5]
        pks_to_edit = [item.pk for item in items_to_edit]

        rsp = self.client.get(
            self.url,
            HTTP_SELECTED_ITEMS=','.join([str(pk) for pk in pks_to_edit])
        )
        self.assertEqual(200, rsp.status_code)
        form = rsp.context['form']
        self.assertIn('supplier', form.fields)
        self.assertNotIn('weight', form.fields)

    def test_post(self):
        # Pass changes and package item pks in a form
        # Selected package items ought to be updated
        donor1 = DonorFactory()
        donor2 = DonorFactory()
        supplier1 = SupplierFactory()
        supplier2 = SupplierFactory()
        pkg = PackageFactory(shipment=self.shipment)
        pkg_items = [PackageItemFactory(package=pkg, supplier=supplier1, donor=donor1)
                     for i in range(10)]
        items_to_edit = pkg_items[:5]
        pks_to_edit = [item.pk for item in items_to_edit]

        data = {
            'donor': donor2.pk,
            'donor_t1': '',
            'supplier': supplier2.pk,
            'item_category': '',
            'selected_items': ','.join([str(pk) for pk in pks_to_edit]),
        }
        rsp = self.client.post(
            self.url,
            data=data,
        )
        self.assertEqual(200, rsp.status_code)
        # refresh package item objects from database
        pkg_items = [PackageItem.objects.get(pk=item.pk) for item in pkg_items]
        # check that the right changes were made
        for item in pkg_items:
            if item.pk in pks_to_edit:
                self.assertEqual(item.supplier, supplier2)
                self.assertEqual(item.donor, donor2)
            else:
                self.assertEqual(item.supplier, supplier1)
                self.assertEqual(item.donor, donor1)

    def test_post_extra_comma(self):
        # sometimes we get an extra comma in the list of pks
        pkg = PackageFactory(shipment=self.shipment)
        pkg_items = [PackageItemFactory(package=pkg)
                     for i in range(3)]
        items_to_edit = pkg_items[:2]
        pks_to_edit = [item.pk for item in items_to_edit]

        data = {
            'donor': '',
            'donor_t1': '',
            'supplier': '',
            'item_category': '',
            'selected_items': ','.join([str(pk) for pk in pks_to_edit]),
        }
        # Append the extra comma that was breaking us
        data['selected_items'] += ','
        rsp = self.client.post(
            self.url,
            data=data,
        )
        self.assertEqual(200, rsp.status_code)

    def test_just_partner(self):
        # Partner may not edit package items
        self.just_partner()
        rsp = self.client.get(self.url)
        self.assertNoPermission(rsp)


@override_settings(ONA_FORM_IDS=[123, 456], ONA_DEVICEID_VERIFICATION_FORM_ID=111)
class ShipmentDashboardViewTest(BaseViewTestCase):
    def setUp(self):
        super(ShipmentDashboardViewTest, self).setUp()
        self.package = PackageFactory(shipment=self.shipment, code=QR_CODE)
        form_data = PackageScanFormSubmission(json.loads(PACKAGE_DATA))
        FormSubmission.from_ona_form_data(form_data)
        self.url = reverse('shipments_dashboard')

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        ctx = rsp.context
        self.assertEqual(self.shipment.description, ctx['shipments'][0].description)

    def test_get_ajax(self):
        kwargs = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        get_data = {'type': 'shipment', 'pk': self.shipment.pk}
        rsp = self.client.get(self.url, get_data, **kwargs)
        self.assertEqual(200, rsp.status_code)
        json_string = rsp.content
        data = json.loads(json_string)
        self.assertEqual(data['undelivered']['packages']['pkg_count'], 1)
        self.assertIsNone(data['delivered']['packages']['pkg_count'])
        self.shipment.status = Shipment.STATUS_RECEIVED
        self.shipment.save()
        rsp = self.client.get(self.url, get_data, **kwargs)
        self.assertEqual(200, rsp.status_code)
        json_string = rsp.content
        data = json.loads(json_string)
        self.assertEqual(data['delivered']['packages']['pkg_count'], 1)
        self.assertIsNone(data['undelivered']['packages']['pkg_count'])

    def test_just_partner(self):
        # Partner may not view another's shipment
        # For this view, means other shipments are omitted from the view
        self.just_partner()
        self.shipment.partner = CtsUserFactory()
        self.shipment.save()
        rsp = self.client.get(self.url)
        context = rsp.context
        shipments = context['shipments']
        self.assertNotIn(self.shipment, shipments)


@override_settings(ONA_FORM_IDS=[123, 456], ONA_DEVICEID_VERIFICATION_FORM_ID=111)
class ShipmentPackageMapViewTest(BaseViewTestCase):
    def setUp(self):
        super(ShipmentPackageMapViewTest, self).setUp()
        self.package = PackageFactory(shipment=self.shipment, code=QR_CODE)
        form_data = PackageScanFormSubmission(json.loads(PACKAGE_DATA))
        FormSubmission.from_ona_form_data(form_data)
        self.url = reverse('shipments_package_map', kwargs={'pk': self.package.pk})

    def test_get(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        ctx = rsp.context
        self.assertEqual(ctx['package'], self.package)

    def test_get_ajax(self):
        kwargs = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        rsp = self.client.get(self.url, **kwargs)
        self.assertEqual(200, rsp.status_code)
        json_string = rsp.content
        data = json.loads(json_string)
        self.assertEqual(self.package.shipment.__unicode__(), data['descr'])

    def test_just_partner(self):
        # Partner may not view another's shipment
        self.just_partner()
        user2 = CtsUserFactory()
        self.shipment.partner = user2
        self.shipment.save()
        rsp = self.client.get(self.url)
        self.assertEqual(404, rsp.status_code)


class ShipmentPackagesViewTest(BaseViewTestCase):
    def setUp(self):
        super(ShipmentPackagesViewTest, self).setUp()
        self.url = reverse('shipment_packages', args=(self.shipment.pk,))
        self.package = PackageFactory(shipment=self.shipment, code=QR_CODE)

    def test_just_partner(self):
        self.just_partner()
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
