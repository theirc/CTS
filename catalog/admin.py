from django.contrib import admin

from catalog.models import CatalogItem, ItemCategory, Donor, Supplier, \
    DonorCode, Transporter


class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ['item_code', 'description', 'price_usd', 'price_local',
                    'item_category', 'donor', 'supplier', 'weight', 'unit']
    list_filter = ['item_category', 'donor', 'supplier']


admin.site.register(CatalogItem, CatalogItemAdmin)
admin.site.register(ItemCategory)
admin.site.register(
    Donor,
    list_display=['name'],
    list_filter=['t1_codes', 't3_codes'])
admin.site.register(DonorCode, list_filter=['donor_code_type'])
admin.site.register(Supplier)
admin.site.register(Transporter)
