from decimal import Decimal
import io
import os
from tempfile import NamedTemporaryFile

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from mock import patch

from accounts.models import ROLE_PARTNER, ROLE_OFFICER, ROLE_COORDINATOR
from accounts.tests.factories import CtsUserFactory
from accounts.utils import bootstrap_permissions
from catalog.models import CatalogItem, Transporter, Supplier, Donor, ItemCategory, \
    DonorCode
from catalog.tests.factories import ItemCategoryFactory, CatalogItemFactory, \
    TransporterFactory, SupplierFactory, DonorFactory, DonorCodeT1Factory
from catalog.utils import CatalogImportFailure
from catalog.forms import MAX_QUANTITY
from shipments.models import KitItem, Kit
from shipments.tests.factories import KitFactory, KitItemFactory, PackageItemFactory


class CatalogViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(CatalogViewTest, cls).setUpClass()
        bootstrap_permissions()

    def setUp(self):
        super(CatalogViewTest, self).setUp()
        self.user = CtsUserFactory(email="joe@example.com", password="6pack", role=ROLE_OFFICER)
        assert self.client.login(email="joe@example.com", password="6pack")

    def test_login_required(self):
        self.client.logout()
        rsp = self.client.get(reverse('catalog_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('catalog_list')
        self.assertRedirects(rsp, expected_url)

    def test_role_required(self):
        # Need OFFICER to work with catalog
        self.user.role = ROLE_PARTNER
        self.user.save()
        rsp = self.client.get(reverse('catalog_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('catalog_list')
        self.assertRedirects(rsp, expected_url)

    def test_list(self):
        cat = ItemCategoryFactory()
        description = "The meow of a cat"
        CatalogItemFactory(item_category=cat, description=description)
        rsp = self.client.get(reverse('catalog_list'))
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, description, msg_prefix=rsp.content.decode('utf-8'))

    def test_create(self):
        # Create an item
        ItemCategoryFactory(name="horse")
        ItemCategoryFactory(name="snowcat")
        cat = ItemCategoryFactory(name="cat")
        ItemCategoryFactory(name="catapult")
        description = "The meow of a cat"
        # Get the form page
        url = reverse('new_catalog_item_modal')
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertIn('form', rsp.context)
        # Submit the new object
        data = {
            'item_code': '007',
            'description': description,
            'unit': 'purr',
            'weight': str(1.005),
            'price_local': '1.23',
            'price_usd': '4.072',
            'item_category': cat.name.upper(),
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors.as_text())
        self.assertEqual(rsp.status_code, 200)
        item = CatalogItem.objects.get(description=description)
        self.assertEqual(cat, item.item_category)
        self.assertEqual('007', item.item_code)
        self.assertEqual(1.005, item.weight)
        self.assertEqual(Decimal('4.072'), item.price_usd)

    def test_update(self):
        # Update an item
        cat = ItemCategoryFactory()
        description = "The meow of a cat"
        item = CatalogItemFactory(item_category=cat, description=description)
        url = reverse('edit_catalog_item_modal', args=[item.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Submit the new object
        description2 = "The bark of a dog"
        data = {
            'item_code': item.item_code,
            'description': description2,
            'unit': 'purr',
            'weight': str(1.005),
            'price_local': '1.23',
            'price_usd': '4.07',
            'item_category': cat.pk,
            'quantity': 3,
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(rsp.status_code, 200)
        item2 = CatalogItem.objects.get(description=description2)
        self.assertEqual(item.pk, item2.pk)

    def test_delete(self):
        # Delete an item
        cat = ItemCategoryFactory()
        description = "The meow of a cat"
        item = CatalogItemFactory(item_category=cat, description=description)
        url = reverse('catalog_delete', args=[item.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, 'Confirm')
        CatalogItem.objects.get(pk=item.pk)
        # Now delete it!
        rsp = self.client.post(url)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertRedirects(rsp, reverse('catalog_list'))
        self.assertFalse(CatalogItem.objects.filter(pk=item.pk).exists())

    def test_price_validator(self):
        # No negative price
        cat = ItemCategoryFactory()
        price_local = 5.000
        item = CatalogItemFactory(item_category=cat, price_local=price_local)
        url = reverse('edit_catalog_item_modal', args=[item.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Submit the new object
        data = {
            'item_code': item.item_code,
            'description': 'desc',
            'unit': 'purr',
            'weight': str(item.weight),
            'price_local': '-1.23',
            'price_usd': '4.07',
            'item_category': cat.pk,
        }
        rsp = self.client.post(url, data=data)
        self.assertEqual(400, rsp.status_code)
        self.assertIn('Ensure this value is greater than', rsp.context['form'].errors.as_text())

    def test_import_view_error(self):
        # Catalog import raises an error. We respond with 400 and the page displays the error.
        url = reverse('catalog_import_modal')

        # We're going to mock the catalog import, so the spreadsheet code will
        # never look at the "file" we upload. But the form validation will at least
        # check that it's not empty, so we need to upload at least 1 byte to get
        # past that.

        fp = io.BytesIO(b'1')
        setattr(fp, 'name', 'fakefilename.xls')
        with patch('catalog.views.catalog_import') as mock_import:
            mock_import.side_effect = CatalogImportFailure(["Killer bunny"])
            rsp = self.client.post(url, {'file': fp})
        self.assertContains(rsp, "Killer bunny", status_code=400)

    def test_import_view_okay(self):
        # Catalog import succeeds, apparently. We display how many records were "imported".
        url = reverse('catalog_import_modal')

        fp = io.BytesIO(b'1')
        setattr(fp, 'name', 'fakefilename.xls')
        with patch('catalog.views.catalog_import') as mock_import:
            mock_import.return_value = 666
            rsp = self.client.post(url, {'file': fp}, follow=True)
        self.assertContains(rsp, '666')

    @override_settings(FILE_UPLOAD_MAX_MEMORY_SIZE=1000)
    def test_import_large_file(self):
        # Not actually importing the large file, but making sure the view can handle it
        url = reverse('catalog_import_modal')
        path = None
        try:
            tmpf = NamedTemporaryFile(mode='wb', delete=False)
            path = tmpf.name
            tmpf.write(b'1' * 1001)
            tmpf.close()
            fp = open(path, 'rb')
            with patch('catalog.views.catalog_import') as mock_import:
                mock_import.return_value = 666
                rsp = self.client.post(url, {'file': fp}, follow=True)
            self.assertContains(rsp, '666')
        finally:
            if path:
                os.remove(path)

    def test_edit_modal(self):
        item = CatalogItemFactory()
        url = reverse('edit_catalog_item_modal', kwargs={'pk': item.pk})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'catalog/catalogitem_edit_modal.html')

    def test_add_item_to_kit(self):
        item1 = CatalogItemFactory()
        kit = KitFactory()
        quantity = 500
        url = reverse('add_item_to_kit', args=[kit.pk, item1.pk, quantity])
        rsp = self.client.post(url)
        self.assertEqual(200, rsp.status_code)
        kit_item = KitItem.objects.get(kit=kit, catalog_item=item1)
        self.assertEqual(quantity, kit_item.quantity)

    def test_add_more_item_to_kit(self):
        item1 = CatalogItemFactory()
        kit = KitFactory()
        # Start with some in the kit
        KitItemFactory(kit=kit, catalog_item=item1, quantity=100)
        quantity = 500
        url = reverse('add_item_to_kit', args=[kit.pk, item1.pk, quantity])
        rsp = self.client.post(url)
        self.assertEqual(200, rsp.status_code)
        kit_item = KitItem.objects.get(kit=kit, catalog_item=item1)
        self.assertEqual(600, kit_item.quantity)

    def test_add_too_many_of_item_to_kit(self):
        item1 = CatalogItemFactory()
        kit = KitFactory()
        quantity = MAX_QUANTITY + 1
        url = reverse('add_item_to_kit', args=[kit.pk, item1.pk, quantity])
        rsp = self.client.post(url)
        self.assertEqual(400, rsp.status_code)

    def test_add_items_to_kit(self):
        item1 = CatalogItemFactory()
        item2 = CatalogItemFactory()
        kit = KitFactory()
        quantity1 = 50
        quantity2 = 60
        url = reverse('catalog_list')
        data = {
            'selected_kit': kit.pk,
            'quantity-%d' % item1.pk: quantity1,
            'quantity-%d' % item2.pk: quantity2,
        }
        rsp = self.client.post(url, data)
        self.assertEqual(302, rsp.status_code)
        kit_item = KitItem.objects.get(kit=kit, catalog_item=item1)
        self.assertEqual(quantity1, kit_item.quantity)
        kit_item = KitItem.objects.get(kit=kit, catalog_item=item2)
        self.assertEqual(quantity2, kit_item.quantity)

    def test_add_too_many_items_to_kit(self):
        item1 = CatalogItemFactory()
        item2 = CatalogItemFactory()
        kit = KitFactory()
        quantity1 = 50
        quantity2 = MAX_QUANTITY + 1
        url = reverse('catalog_list')
        data = {
            'selected_kit': kit.pk,
            'quantity-%d' % item1.pk: quantity1,
            'quantity-%d' % item2.pk: quantity2,
        }
        rsp = self.client.post(url, data)
        self.assertEqual(400, rsp.status_code)
        with self.assertRaises(KitItem.DoesNotExist):
            KitItem.objects.get(kit=kit, catalog_item=item1)
        with self.assertRaises(KitItem.DoesNotExist):
            KitItem.objects.get(kit=kit, catalog_item=item2)


class TransporterViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TransporterViewTest, cls).setUpClass()
        bootstrap_permissions()

    def setUp(self):
        super(TransporterViewTest, self).setUp()
        self.user = CtsUserFactory(email="joe@example.com", password="6pack")
        assert self.client.login(email="joe@example.com", password="6pack")

    def test_login_required(self):
        self.client.logout()
        rsp = self.client.get(reverse('transporter_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('transporter_list')
        self.assertRedirects(rsp, expected_url)

    def test_role_required(self):
        # Need coordinator role
        self.user.role = ROLE_OFFICER
        self.user.save()
        rsp = self.client.get(reverse('transporter_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('transporter_list')
        self.assertRedirects(rsp, expected_url)

    def test_list(self):
        transporter = TransporterFactory()
        rsp = self.client.get(reverse('transporter_list'))
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, transporter.name, msg_prefix=rsp.content.decode('utf-8'))

    def test_create(self):
        # Create a transporter
        # Get the form page
        url = reverse('new_transporter_modal')
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertIn('form', rsp.context)
        # Submit the new object
        data = {
            'name': 'test',
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors.as_text())
        self.assertEqual(rsp.status_code, 200)
        Transporter.objects.get(name='test')

    def test_update(self):
        # Update a transporter
        transporter = TransporterFactory()
        url = reverse('edit_transporter_modal', args=[transporter.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Submit the new object
        name = "edited"
        data = {
            'name': name,
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(rsp.status_code, 200)
        transporter2 = Transporter.objects.get(name=name)
        self.assertEqual(transporter.pk, transporter2.pk)

    def test_delete(self):
        # Delete a transporter
        transporter = TransporterFactory()
        url = reverse('transporter_delete', args=[transporter.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, 'Confirm')
        Transporter.objects.get(pk=transporter.pk)
        # Now delete it!
        rsp = self.client.post(url)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertRedirects(rsp, reverse('transporter_list'))
        self.assertFalse(Transporter.objects.filter(pk=transporter.pk).exists())

    def test_edit_modal(self):
        transporter = TransporterFactory()
        url = reverse('edit_transporter_modal', kwargs={'pk': transporter.pk})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'catalog/transporter_edit_modal.html')


class SupplierViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(SupplierViewTest, cls).setUpClass()
        bootstrap_permissions()

    def setUp(self):
        super(SupplierViewTest, self).setUp()
        self.user = CtsUserFactory(email="joe@example.com", password="6pack")
        assert self.client.login(email="joe@example.com", password="6pack")

    def test_login_required(self):
        self.client.logout()
        rsp = self.client.get(reverse('supplier_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('supplier_list')
        self.assertRedirects(rsp, expected_url)

    def test_role_required(self):
        # Need coordinator role
        self.user.role = ROLE_OFFICER
        self.user.save()
        rsp = self.client.get(reverse('supplier_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('supplier_list')
        self.assertRedirects(rsp, expected_url)

    def test_list(self):
        supplier = SupplierFactory()
        rsp = self.client.get(reverse('supplier_list'))
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, supplier.name, msg_prefix=rsp.content.decode('utf-8'))

    def test_create(self):
        # Create a supplier
        # Get the form page
        url = reverse('new_supplier_modal')
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertIn('form', rsp.context)
        # Submit the new object
        data = {
            'name': 'test',
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors.as_text())
        self.assertEqual(rsp.status_code, 200)
        Supplier.objects.get(name='test')

    def test_update(self):
        # Update a supplier
        supplier = SupplierFactory()
        url = reverse('edit_supplier_modal', args=[supplier.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Submit the new object
        name = "edited"
        data = {
            'name': name,
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(rsp.status_code, 200)
        supplier2 = Supplier.objects.get(name=name)
        self.assertEqual(supplier.pk, supplier2.pk)

    def test_delete(self):
        # Delete a supplier
        supplier = SupplierFactory()
        url = reverse('supplier_delete', args=[supplier.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, 'Confirm')
        Supplier.objects.get(pk=supplier.pk)
        # Now delete it!
        rsp = self.client.post(url)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertRedirects(rsp, reverse('supplier_list'))
        self.assertFalse(Supplier.objects.filter(pk=supplier.pk).exists())

    def test_edit_modal(self):
        supplier = SupplierFactory()
        url = reverse('edit_supplier_modal', kwargs={'pk': supplier.pk})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'catalog/supplier_edit_modal.html')


class CategoryViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(CategoryViewTest, cls).setUpClass()
        bootstrap_permissions()

    def setUp(self):
        super(CategoryViewTest, self).setUp()
        self.user = CtsUserFactory(email="joe@example.com", password="6pack", role=ROLE_OFFICER)
        assert self.client.login(email="joe@example.com", password="6pack")

    def test_login_required(self):
        self.client.logout()
        rsp = self.client.get(reverse('category_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('category_list')
        self.assertRedirects(rsp, expected_url)

    def test_role_required(self):
        # Need officer role
        self.user.role = ROLE_PARTNER
        self.user.save()
        rsp = self.client.get(reverse('category_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('category_list')
        self.assertRedirects(rsp, expected_url)

    def test_list(self):
        category = ItemCategoryFactory()
        rsp = self.client.get(reverse('category_list'))
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, category.name, msg_prefix=rsp.content.decode('utf-8'))

    def test_create(self):
        # Create a category
        # Get the form page
        url = reverse('new_category_modal')
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertIn('form', rsp.context)
        # Submit the new object
        data = {
            'name': 'test',
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors.as_text())
        self.assertEqual(rsp.status_code, 200)
        ItemCategory.objects.get(name='test')

    def test_update(self):
        # Update a category
        category = ItemCategoryFactory()
        url = reverse('edit_category_modal', args=[category.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Submit the new object
        name = "edited"
        data = {
            'name': name,
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(rsp.status_code, 200)
        category2 = ItemCategory.objects.get(name=name)
        self.assertEqual(category.pk, category2.pk)

    def test_delete(self):
        # Delete a category
        category = ItemCategoryFactory()
        url = reverse('category_delete', args=[category.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, 'Confirm')
        ItemCategory.objects.get(pk=category.pk)
        # Now delete it!
        rsp = self.client.post(url)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertRedirects(rsp, reverse('category_list'))
        self.assertFalse(ItemCategory.objects.filter(pk=category.pk).exists())

    def test_edit_modal(self):
        category = ItemCategoryFactory()
        url = reverse('edit_category_modal', kwargs={'pk': category.pk})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'catalog/category_edit_modal.html')


class DonorViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(DonorViewTest, cls).setUpClass()
        bootstrap_permissions()

    def setUp(self):
        super(DonorViewTest, self).setUp()
        self.user = CtsUserFactory(email="joe@example.com", password="6pack")
        assert self.client.login(email="joe@example.com", password="6pack")

    def test_login_required(self):
        self.client.logout()
        rsp = self.client.get(reverse('donor_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('donor_list')
        self.assertRedirects(rsp, expected_url)

    def test_role_required(self):
        # Need coordinator role
        self.user.role = ROLE_OFFICER
        self.user.save()
        rsp = self.client.get(reverse('donor_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('donor_list')
        self.assertRedirects(rsp, expected_url)

    def test_list(self):
        donor = DonorFactory()
        rsp = self.client.get(reverse('donor_list'))
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, donor.name, msg_prefix=rsp.content.decode('utf-8'))

    def test_create(self):
        # Create a donor
        # Get the form page
        url = reverse('new_donor_modal')
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertIn('form', rsp.context)
        # Submit the new object
        data = {
            'name': 'test',
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors.as_text())
        self.assertEqual(rsp.status_code, 200)
        Donor.objects.get(name='test')

    def test_update(self):
        # Update a donor
        donor = DonorFactory()
        url = reverse('edit_donor_modal', args=[donor.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Submit the new object
        name = "edited"
        data = {
            'name': name,
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(rsp.status_code, 200)
        donor2 = Donor.objects.get(name=name)
        self.assertEqual(donor.pk, donor2.pk)

    def test_update_and_create_new_codes(self):
        # Update a donor, create some new codes, and add them to the donor
        donor = DonorFactory()
        url = reverse('edit_donor_modal', args=[donor.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        t1_codeA = DonorCode.objects.create(code='t1A', donor_code_type=DonorCode.T1)
        t1_codeB = DonorCode.objects.create(code='t1B', donor_code_type=DonorCode.T1)
        t3_codeA = DonorCode.objects.create(code='t1A', donor_code_type=DonorCode.T3)
        # Submit the new object
        name = "edited"
        data = {
            'name': name,
            't1_codes_1': [t1_codeA.pk, t1_codeB.pk],
            'new_t1_codes': 'New code C, t1A',
            't3_codes_1': [t3_codeA.pk],
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(rsp.status_code, 200)
        donor2 = Donor.objects.get(name=name)
        self.assertEqual(donor.pk, donor2.pk)
        code_c = DonorCode.objects.get(code='New code C', donor_code_type=DonorCode.T1)
        self.assertIn(code_c, donor2.t1_codes.all())
        self.assertIn(t1_codeA, donor2.t1_codes.all())
        self.assertIn(t3_codeA, donor2.t3_codes.all())

    def test_delete(self):
        # Delete a donor
        donor = DonorFactory()
        url = reverse('donor_delete', args=[donor.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, 'Confirm')
        Donor.objects.get(pk=donor.pk)
        # Now delete it!
        rsp = self.client.post(url)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertRedirects(rsp, reverse('donor_list'))
        self.assertFalse(Donor.objects.filter(pk=donor.pk).exists())

    def test_edit_modal(self):
        donor = DonorFactory()
        url = reverse('edit_donor_modal', kwargs={'pk': donor.pk})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'catalog/donor_edit_modal.html')


class DonorCodeViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(DonorCodeViewTest, cls).setUpClass()
        bootstrap_permissions()

    def setUp(self):
        super(DonorCodeViewTest, self).setUp()
        self.user = CtsUserFactory(email="joe@example.com", password="6pack", role=ROLE_COORDINATOR)
        assert self.client.login(email="joe@example.com", password="6pack")

    def test_login_required(self):
        self.client.logout()
        rsp = self.client.get(reverse('donorcode_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('donorcode_list')
        self.assertRedirects(rsp, expected_url)

    def test_role_required(self):
        # Need officer role
        self.user.role = ROLE_PARTNER
        self.user.save()
        rsp = self.client.get(reverse('donorcode_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('donorcode_list')
        self.assertRedirects(rsp, expected_url)

    def test_list(self):
        donorcode = DonorCodeT1Factory()
        rsp = self.client.get(reverse('donorcode_list'))
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, donorcode.code, msg_prefix=rsp.content.decode('utf-8'))

    def test_create(self):
        # Create a donorcode
        # Get the form page
        url = reverse('new_donorcode_modal')
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertIn('form', rsp.context)
        # Submit the new object
        data = {
            'code': 'test',
            'donor_code_type': 't1',
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors.as_text())
        self.assertEqual(rsp.status_code, 200)
        DonorCode.objects.get(code='test')

    def test_update(self):
        # Update a donorcode
        donorcode = DonorCodeT1Factory()
        url = reverse('edit_donorcode_modal', args=[donorcode.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Submit the new object
        code = "edited"
        data = {
            'code': code,
            'donor_code_type': 't1',
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(rsp.status_code, 200)
        donorcode2 = DonorCode.objects.get(code=code)
        self.assertEqual(donorcode.pk, donorcode2.pk)

    def test_delete(self):
        # Delete a donorcode
        donorcode = DonorCodeT1Factory()
        url = reverse('donorcode_delete', args=[donorcode.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, 'Confirm')
        DonorCode.objects.get(pk=donorcode.pk)
        # Now delete it!
        rsp = self.client.post(url)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertRedirects(rsp, reverse('donorcode_list'))
        self.assertFalse(DonorCode.objects.filter(pk=donorcode.pk).exists())

    def test_edit_modal(self):
        donorcode = DonorCodeT1Factory()
        url = reverse('edit_donorcode_modal', kwargs={'pk': donorcode.pk})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'catalog/donorcode_edit_modal.html')


class KitDeleteViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(KitDeleteViewTest, cls).setUpClass()
        bootstrap_permissions()

    def setUp(self):
        super(KitDeleteViewTest, self).setUp()
        self.user = CtsUserFactory(email="joe@example.com", password="6pack", role=ROLE_COORDINATOR)
        assert self.client.login(email="joe@example.com", password="6pack")
        assert self.user.has_perm('shipments.delete_kit')

    def test_delete_referenced_kit(self):
        kit = KitFactory()
        KitItemFactory(kit=kit)
        PackageItemFactory(package__kit=kit)

        url = reverse('kit_delete', kwargs={'pk': kit.pk})
        rsp = self.client.post(url)
        success_url = reverse('catalog_list')
        self.assertRedirects(rsp, success_url)
        self.assertFalse(Kit.objects.filter(pk=kit.pk).exists())
