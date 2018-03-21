from collections import OrderedDict

from django.test import TestCase

from mock import patch, Mock

from catalog.models import CatalogItem
from catalog.tests.factories import ItemCategoryFactory, DonorFactory, SupplierFactory, \
    DonorCodeT1Factory
from catalog.utils import _catalog_import_from_simple_sheet, SimpleSheet, IMPORT_COLUMN_NAMES, \
    CatalogImportFailure, catalog_import, MAX_IMPORT_ERRORS


class MockSimpleSheet(object):
    def __init__(self, rows=None, col_names=None):
        self.data_rows = rows or []
        self.col_names = col_names or IMPORT_COLUMN_NAMES

    def column_names(self):
        return self.col_names

    def rows(self):
        for i, row in enumerate(self.data_rows):
            yield i + 1, row


class ImportTest(TestCase):
    # These tests verify that the catalog import function does the right thing depending
    # on what data it gets from the SimpleSheet object. We don't need to test that xlrd
    # can correctly read a spreadsheet as part of our tests, so we don't bother with that.
    def setUp(self):
        self.cat = ItemCategoryFactory(name='test category')
        self.cat_name = self.cat.name
        self.donor_t1 = DonorCodeT1Factory(code='Donor t1 code')
        self.donor = DonorFactory(name='Donor 1', t1_codes=[self.donor_t1])
        supplier = SupplierFactory(name='Supplier 27')
        self.valid_row = {
            'item_code': '0001',
            'item_category': self.cat_name,
            'description': 'thing',
            'donor': self.donor.name,
            'donor_t1': self.donor_t1.code,
            'supplier': supplier.name,
            'weight': '3.14',
            'unit': 'pair of pants',
            'price_local': '2.34',
            'price_usd': '1.23',
        }

    def test_valid(self):
        sheet = MockSimpleSheet([self.valid_row])
        _catalog_import_from_simple_sheet(sheet)
        item = CatalogItem.objects.get(item_code=self.valid_row['item_code'])
        self.assertEqual(self.donor_t1, item.donor_t1)

    def test_t1_doesnt_match_donor(self):
        donor = self.donor
        donor.t1_codes.clear()
        donor.t1_codes.add(DonorCodeT1Factory(code='Another T1'))
        sheet = MockSimpleSheet([self.valid_row])
        _catalog_import_from_simple_sheet(sheet)
        # Form should add the missing t1 donor to the donor's t1_codes
        self.assertTrue(self.donor_t1 in self.donor.t1_codes.all())

    def test_no_t1_specified(self):
        row = self.valid_row.copy()
        row['donor_t1'] = ''
        sheet = MockSimpleSheet([row])
        _catalog_import_from_simple_sheet(sheet)
        self.assertTrue(CatalogItem.objects.filter(item_code=self.valid_row['item_code']).exists())

    def test_missing_columns(self):
        # mock sheet that's missing some columns
        sheet = MockSimpleSheet(col_names=['one', 'two', 'description'])
        with self.assertRaises(CatalogImportFailure):
            _catalog_import_from_simple_sheet(sheet)

    def test_exception_during_import(self):
        sheet = MockSimpleSheet([self.valid_row])
        with patch('catalog.utils.CatalogItemImportForm') as mock_form:
            mock_form.side_effect = TypeError
            with self.assertRaises(CatalogImportFailure):
                _catalog_import_from_simple_sheet(sheet)

    def test_max_errors(self):
        invalid_row = self.valid_row.copy()
        invalid_row['description'] = ''  # required field
        sheet = MockSimpleSheet([invalid_row for x in range(MAX_IMPORT_ERRORS - 1)])
        expected_msg = "Giving up after %d errors" % MAX_IMPORT_ERRORS
        try:
            _catalog_import_from_simple_sheet(sheet)
        except CatalogImportFailure as e:
            self.assertNotIn(expected_msg, e.errlist)
        else:
            self.fail("Expected CatalogImportFailure")
        sheet = MockSimpleSheet([invalid_row for x in range(MAX_IMPORT_ERRORS + 10)])
        try:
            _catalog_import_from_simple_sheet(sheet)
        except CatalogImportFailure as e:
            self.assertIn(expected_msg, e.errlist)
            self.assertEqual(MAX_IMPORT_ERRORS + 1, len(e.errlist))
        else:
            self.fail("Expected CatalogImportFailure")

    def test_catalog_import_function(self):
        path = 'sdiuyf'
        with patch('catalog.utils.SimpleSheet') as mock_sheet:
            with patch('catalog.utils._catalog_import_from_simple_sheet') as mock_import:
                mock_import.return_value = 666
                retval = catalog_import(path)
        self.assertEqual(666, retval)
        mock_sheet.assert_called_with(path, 0)

    def test_catalog_import_function_sheet_fails(self):
        path = 'sdiuyf'
        with patch('catalog.utils.SimpleSheet') as mock_sheet:
            mock_sheet.side_effect = ValueError
            with patch('catalog.utils._catalog_import_from_simple_sheet'):
                with self.assertRaises(CatalogImportFailure):
                    catalog_import(path)
        mock_sheet.assert_called_with(path, 0)


class SimpleSheetTest(TestCase):
    def test_simple_sheet(self):
        # Mock some xlrd responses to see if SimpleSheet works okay
        mock_sheet = Mock()
        mock_sheet.nrows = 3
        mock_sheet.row_values.return_value = IMPORT_COLUMN_NAMES
        mock_book = Mock()
        mock_book.nsheets = 5
        mock_book.sheet_by_index.return_value = mock_sheet

        with patch('catalog.utils.xlrd') as mock_xlrd:
            mock_xlrd.open_workbook.return_value = mock_book
            s = SimpleSheet('filename', 3)

        self.assertEqual(s.column_names(), IMPORT_COLUMN_NAMES)
        rows = s.rows()
        row_number, row = rows.next()
        self.assertEqual(2, row_number)
        self.assertEqual(row, OrderedDict(zip(IMPORT_COLUMN_NAMES, IMPORT_COLUMN_NAMES)))
        row_number, row = rows.next()
        self.assertEqual(3, row_number)
        self.assertEqual(row, OrderedDict(zip(IMPORT_COLUMN_NAMES, IMPORT_COLUMN_NAMES)))
        with self.assertRaises(StopIteration):
            row_number, row = rows.next()

    def test_bad_sheet_number(self):
        mock_book = Mock()
        mock_book.nsheets = 2

        with patch('catalog.utils.xlrd') as mock_xlrd:
            mock_xlrd.open_workbook.return_value = mock_book
            with self.assertRaises(ValueError):
                SimpleSheet('filename', 3)

    def test_empty_sheet(self):
        mock_sheet = Mock()
        mock_sheet.nrows = 0
        mock_sheet.row_values.return_value = IMPORT_COLUMN_NAMES
        mock_book = Mock()
        mock_book.nsheets = 5
        mock_book.sheet_by_index.return_value = mock_sheet

        with patch('catalog.utils.xlrd') as mock_xlrd:
            mock_xlrd.open_workbook.return_value = mock_book
            with self.assertRaises(ValueError):
                SimpleSheet('filename', 3)
