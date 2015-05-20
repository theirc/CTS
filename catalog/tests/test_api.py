import json

from accounts.tests.factories import CtsUserFactory
from accounts.utils import bootstrap_permissions
from api.tests import BaseAPITest
from catalog.tests.factories import CatalogItemFactory, ItemCategoryFactory


class CatalogAPITest(BaseAPITest):
    @classmethod
    def setUpClass(cls):
        bootstrap_permissions()

    def setUp(self):
        self.email = 'ginger@example.com'
        self.password = 'rogers'
        self.user = CtsUserFactory(email=self.email,
                                   password=self.password)

    def test_list_items(self):
        CatalogItemFactory(description='item1')
        CatalogItemFactory(description='item2')
        rsp = self.call_api('/api/catalog/items/')
        self.assertEqual(200, rsp.status_code)
        data = json.loads(rsp.content)['results']
        item_descriptions = [item['description'] for item in data]
        self.assertIn('item1', item_descriptions)
        self.assertIn('item2', item_descriptions)

    def test_get_item(self):
        item1 = CatalogItemFactory(description='item1')
        CatalogItemFactory(description='item2')
        rsp = self.call_api('/api/catalog/items/%d/' % item1.pk)
        self.assertEqual(200, rsp.status_code)
        data = json.loads(rsp.content)
        self.assertEqual(item1.description, data['description'])

    def test_list_categories(self):
        ItemCategoryFactory(name="cat1")
        ItemCategoryFactory(name="cat2")
        rsp = self.call_api('/api/catalog/categories/')
        self.assertEqual(200, rsp.status_code)
        data = json.loads(rsp.content)['results']
        names = [cat['name'] for cat in data]
        self.assertIn('cat1', names)

    def test_get_category(self):
        cat1 = ItemCategoryFactory(name="cat1")
        rsp = self.call_api('/api/catalog/categories/%d/' % cat1.pk)
        self.assertEqual(200, rsp.status_code)
        data = json.loads(rsp.content)
        self.assertEqual(cat1.name, data['name'])
