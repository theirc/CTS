from selectable.base import ModelLookup
from selectable.registry import registry

from catalog.models import DonorCode, ItemCategory, CatalogItem


class T1DonorCodeLookup(ModelLookup):
    model = DonorCode
    search_fields = ('code__icontains', )
    filters = {'donor_code_type': DonorCode.T1, }


class T3DonorCodeLookup(ModelLookup):
    model = DonorCode
    search_fields = ('code__icontains', )
    filters = {'donor_code_type': DonorCode.T3, }


class ItemCategoryLookup(ModelLookup):
    model = ItemCategory
    search_fields = ('name__icontains', )


class CatalogItemLookup(ModelLookup):
    model = CatalogItem
    search_fields = ('item_code__icontains', 'description__icontains')

    def get_item_label(self, item):
        if item.donor_id:
            return '{} ({})'.format(item.description, item.donor)
        else:
            return item.description


registry.register(T1DonorCodeLookup)
registry.register(T3DonorCodeLookup)
registry.register(ItemCategoryLookup)
registry.register(CatalogItemLookup)
