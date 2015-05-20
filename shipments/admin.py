from django.contrib import admin

from shipments.models import Shipment, Package, PackageItem, Kit, KitItem, PackageScan


admin.site.register(
    Shipment,
    list_display=['description', 'shipment_date', 'get_status_display'],
    list_display_links=['description', 'shipment_date'],
)
admin.site.register(
    Package,
    list_display=['shipment', 'name', 'description', 'number_in_shipment', 'status', 'kit'],
    raw_id_fields=['shipment', 'kit', 'last_scan'],
    search_fields=['name', 'description', 'shipment__description'],
)

admin.site.register(
    PackageItem,
    list_display=['package', 'quantity', 'catalog_item',
                  'description', 'unit', 'price_usd', 'price_local',
                  'item_category', 'donor', 'donor_t1', 'supplier', 'weight',
                  ],
    list_filter=['donor', 'item_category'],
    raw_id_fields=['package', 'catalog_item'],
)


class KitItemInline(admin.TabularInline):
    model = KitItem
    raw_id_fields = ['catalog_item']


class KitAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    inlines = [KitItemInline]
    search_fields = ['name', 'description', 'package__name', 'package__description'],
admin.site.register(Kit, KitAdmin)

admin.site.register(KitItem)


class PackageScanAdmin(admin.ModelAdmin):
    list_display = ['package', 'when', 'longitude', 'latitude', 'altitude', 'accuracy', 'country']
    raw_id_fields = ['package']
    search_fields = ['package__name', 'package__description', 'package__shipment__description',
                     'package__shipment__store_release']

admin.site.register(PackageScan, PackageScanAdmin)
