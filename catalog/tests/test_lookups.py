from django.test import TestCase

from catalog.lookups import CatalogItemLookup
from catalog.tests.factories import CatalogItemFactory


class TestCatalogItemLookup(TestCase):

    def setUp(self):
        super(TestCatalogItemLookup, self).setUp()
        self.lookup = CatalogItemLookup()
        for i in range(5):
            CatalogItemFactory()

    def test_item_code(self):
        item = CatalogItemFactory(item_code='hello world')
        qs = self.lookup.get_query(None, 'hello')
        self.assertEqual(len(qs), 1)
        self.assertEqual(qs.get(), item)

    def test_description(self):
        item = CatalogItemFactory(description='hello world')
        qs = self.lookup.get_query(None, 'hello')
        self.assertEqual(len(qs), 1)
        self.assertEqual(qs.get(), item)
