from django.db.models import Sum

from django_tables2 import Column, DateColumn
from django_tables2_reports.tables import TableReport

from reports.models import DonorCategoryData, DonorShipmentData
from shipments.models import PackageDBView, ShipmentDBView, PackageItemDBView

from .columns import (
    NumberColumn, LocalCurrencyColumn, PercentageColumn, USDCurrencyColumn,
    LocalCurrencyDownloadColumn)


class PackageReportTable(TableReport):

    number_in_shipment = NumberColumn(verbose_name="ID in Shipment")
    num_items = NumberColumn(verbose_name="# Items")
    price_local = LocalCurrencyColumn(verbose_name="Total Price (Local)")
    price_usd = USDCurrencyColumn(verbose_name="Total Price (USD)")

    class Meta:
        model = PackageDBView
        fields = ('shipment.partner.name', 'shipment.shipment_date',
                  'shipment.description', 'number_in_shipment', 'name',
                  'last_scan.country', 'last_scan.when',
                  'get_status_display', 'num_items', 'price_local',
                  'price_usd')

    def __init__(self, *args, **kwargs):
        super(PackageReportTable, self).__init__(*args, **kwargs)
        self.data.verbose_name = "package"
        self.data.verbose_name_plural = "packages"

        self.columns['shipment.partner.name'].column.verbose_name = "Partner"
        self.columns['shipment.description'].column.verbose_name = "Shipment"
        self.columns['name'].column.verbose_name = "Description"
        self.columns['get_status_display'].column.verbose_name = "Status"
        self.columns['last_scan.country'].column.verbose_name = "Last Scan Location"
        self.columns['last_scan.when'].column.verbose_name = "Last Scanned"

    def get_table_footer(self, queryset):
        """Return a dictionary to add to the template context containing
        the table footer values"""
        return queryset.aggregate(
            total_quantity=Sum('num_items'),
            total_local=Sum('price_local'),
            total_usd=Sum('price_usd'),
        )


class PackageDownloadableTable(PackageReportTable):

    price_local = LocalCurrencyDownloadColumn(verbose_name="Total Price (Local)")
    price_usd = NumberColumn(verbose_name="Total Price (USD)")


class DonorByShipmentReportTable(TableReport):

    package_count = NumberColumn()
    item_count = NumberColumn()
    percentage_of_shipment = PercentageColumn()
    price_local = LocalCurrencyColumn()
    price_usd = USDCurrencyColumn()

    class Meta:
        model = DonorShipmentData
        fields = ('shipment.partner.name', 'donor.name',
                  'shipment.shipment_date', 'shipment.description',
                  'shipment.status', 'package_count', 'item_count',
                  'percentage_of_shipment', 'price_local', 'price_usd')

    def __init__(self, *args, **kwargs):
        super(DonorByShipmentReportTable, self).__init__(*args, **kwargs)
        self.data.verbose_name = 'item'
        self.data.verbose_name_plural = 'items'

        self.columns['shipment.partner.name'].column.verbose_name = 'Partner'
        self.columns['donor.name'].column.verbose_name = 'Donor'
        self.columns['shipment.description'].column.verbose_name = 'Shipment'
        self.columns['shipment.status'].column.verbose_name = 'Shipment Status'

    def get_table_footer(self, queryset):
        """Return a dictionary to add to the template context containing
        the table footer values"""
        return queryset.aggregate(
            total_package_count=Sum('package_count'),
            total_item_count=Sum('item_count'),
            total_local=Sum('price_local'),
            total_usd=Sum('price_usd'),
        )


class DonorByShipmentDownloadableTable(DonorByShipmentReportTable):

    price_local = LocalCurrencyDownloadColumn()
    price_usd = NumberColumn()


class DonorByCategoryReportTable(TableReport):

    item_count = NumberColumn()
    total_quantity = NumberColumn()
    price_local = LocalCurrencyColumn()
    price_usd = USDCurrencyColumn()

    class Meta:
        model = DonorCategoryData
        fields = ('donor.name', 'category.name', 'item_count',
                  'total_quantity', 'price_local', 'price_usd')

    def __init__(self, *args, **kwargs):
        super(DonorByCategoryReportTable, self).__init__(*args, **kwargs)

        self.data.verbose_name = 'item'
        self.data.verbose_name_plural = 'items'

        self.columns['donor.name'].column.verbose_name = "Donor"
        self.columns['category.name'].column.verbose_name = "Category"

    def get_table_footer(self, queryset):
        """Return a dictionary to add to the template context containing
        the table footer values"""
        return queryset.aggregate(
            total_item_count=Sum('item_count'),
            total_quantity=Sum('total_quantity'),
            total_local=Sum('price_local'),
            total_usd=Sum('price_usd'),
        )


class DonorByCategoryDownloadableTable(DonorByCategoryReportTable):

    price_local = LocalCurrencyDownloadColumn()
    price_usd = NumberColumn()


class ItemReportTable(TableReport):

    quantity = NumberColumn()
    extended_price_local = LocalCurrencyColumn(verbose_name="Total Price (Local)")
    extended_price_usd = USDCurrencyColumn(verbose_name="Total Price (USD)")

    class Meta:
        model = PackageItemDBView
        fields = ('package.shipment',
                  'package.shipment.partner.name', 'donor', 'item_category',
                  'description', 'quantity', 'package.get_status_display',
                  'extended_price_local', 'extended_price_usd')

    def __init__(self, *args, **kwargs):
        super(ItemReportTable, self).__init__(*args, **kwargs)
        self.columns['package.shipment.partner.name'].column.verbose_name = "Partner"
        self.columns['item_category'].column.verbose_name = "Category"
        self.columns['description'].column.verbose_name = "Item"
        self.columns['package.get_status_display'].column.verbose_name = "Package Status"
        self.columns['package.get_status_display'].column.order_by = 'status'

    def get_table_footer(self, queryset):
        """Return a dictionary to add to the template context containing
        the table footer values"""
        return queryset.aggregate(
            total_quantity=Sum('quantity'),
            total_local=Sum('extended_price_local'),
            total_usd=Sum('extended_price_usd'),
        )


class ItemDownloadableTable(ItemReportTable):

    extended_price_local = LocalCurrencyDownloadColumn(verbose_name="Total Price (Local)")
    extended_price_usd = NumberColumn(verbose_name="Total Price (USD)")


class ShipmentReportTable(TableReport):
    # TODO: Add last scan date/location, package count

    class Meta:
        model = ShipmentDBView
        fields = ('partner.name', 'description', 'shipment_date', 'status')

    def __init__(self, *args, **kwargs):
        super(ShipmentReportTable, self).__init__(*args, **kwargs)
        self.columns['partner.name'].column.verbose_name = "Partner"


class ReceivedItemsByShipmentReportTable(TableReport):
    percent_delivered = Column(accessor="percent_items_received")

    class Meta:
        model = ShipmentDBView
        fields = ('shipment_date', 'description', 'num_items', 'num_received_items')

    def __init__(self, *args, **kwargs):
        super(ReceivedItemsByShipmentReportTable, self).__init__(*args, **kwargs)
        self.columns['num_items'].column.verbose_name = "Item Count"
        self.columns['num_received_items'].column.verbose_name = "Delivered Count"
        self.columns['percent_delivered'].column.verbose_name = "% Delivered"


class ReceivedItemsByDonorOrPartnerReportTable(TableReport):
    item_count = NumberColumn()
    delivered_count = NumberColumn()
    percent_delivered = Column(accessor="percent_items_received")

    class Meta:
        model = DonorShipmentData
        fields = ('shipment.partner.name', 'donor.name',
                  'shipment.shipment_date', 'shipment.description',
                  'item_count', 'delivered_count')

    def __init__(self, *args, **kwargs):
        super(ReceivedItemsByDonorOrPartnerReportTable, self).__init__(*args, **kwargs)
        self.data.verbose_name = 'item'
        self.data.verbose_name_plural = 'items'

        self.columns['shipment.partner.name'].column.verbose_name = 'Partner'
        self.columns['donor.name'].column.verbose_name = 'Donor'
        self.columns['percent_delivered'].column.verbose_name = "% Delivered"
        self.columns['shipment.description'].column.verbose_name = 'Shipment'


class ShipmentMonthlySummaryReportTable(TableReport):
    month = DateColumn(format='m/Y')
    pk__count = NumberColumn()

    def __init__(self, *args, **kwargs):
        super(ShipmentMonthlySummaryReportTable, self).__init__(*args, **kwargs)
        self.data.verbose_name = 'item'
        self.data.verbose_name_plural = 'items'

        self.columns['month'].column.verbose_name = "Month Shipped"
        self.columns['pk__count'].column.verbose_name = 'Shipments'
