import datetime
from operator import methodcaller

from django.conf import settings
from django.forms import CheckboxSelectMultiple

import django_filters

from accounts.models import ROLE_PARTNER, CtsUser
from reports.models import DonorCategoryData, DonorShipmentData
from shipments.models import PackageDBView, ShipmentDBView, PackageItemDBView, Shipment


# EMPTY_LABEL = '---------'


THIS_YEAR = datetime.date.today().year

# This is how we're displaying dates, it'd be confusing to expect
# a different format for input.
DATE_INPUT_FORMATS = ['%m/%d/%Y']
DATE_INPUT_HELP = "(M/D/Y)"


class ReportFilter(django_filters.FilterSet):

    def __init__(self, *args, **kwargs):
        """Tweak some of the filter fields"""
        self.user = kwargs.pop('user')
        super(ReportFilter, self).__init__(*args, **kwargs)
        # Code here used to insert an empty choice label for shipments, but
        # DRF does that for us now.
        if not self.user.has_perm('reports.view_all_partners') and 'partner' in self.filters:
            # Remember the key to use to filter on partners later on
            self.partner_field_name = self.filters['partner'].name
            # And get rid of the user-visible partner filter
            del self.filters['partner']

    @property
    def qs(self):
        qs = super(ReportFilter, self).qs
        if hasattr(self, 'partner_field_name'):
            # We are filtering out other partners
            qs = qs.filter(**{self.partner_field_name: self.user})
        return qs


class PackageReportFilter(ReportFilter):
    partner = django_filters.ModelChoiceFilter(
        name='shipment__partner',
        queryset=CtsUser.objects.filter(role=ROLE_PARTNER).order_by('name')
    )
    status = django_filters.MultipleChoiceFilter(
        choices=Shipment.SHIPMENT_STATUS_CHOICES,
        widget=CheckboxSelectMultiple,
        label="Shipment status",
    )

    class Meta:
        model = PackageDBView
        fields = ('partner', 'shipment', 'status')


class DonorByShipmentReportFilter(ReportFilter):
    shipped_before = django_filters.DateFilter(
        lookup_expr='lte',
        name='shipment__shipment_date',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped before ' + DATE_INPUT_HELP
    )
    shipped_after = django_filters.DateFilter(
        lookup_expr='gte',
        name='shipment__shipment_date',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped after ' + DATE_INPUT_HELP
    )
    partner = django_filters.ModelChoiceFilter(
        name='shipment__partner',
        queryset=CtsUser.objects.filter(role=ROLE_PARTNER).order_by('name')
    )
    status = django_filters.MultipleChoiceFilter(
        name='shipment__status',
        choices=Shipment.SHIPMENT_STATUS_CHOICES,
        widget=CheckboxSelectMultiple,
        label="Shipment status",
    )

    class Meta:
        model = DonorShipmentData
        fields = ('partner', 'donor', 'status')


class DonorByCategoryReportFilter(ReportFilter):
    shipped_before = django_filters.DateFilter(
        lookup_expr='lte',
        name='first_date_shipped',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped before ' + DATE_INPUT_HELP
    )
    shipped_after = django_filters.DateFilter(
        lookup_expr='gte',
        name='last_date_shipped',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped after ' + DATE_INPUT_HELP
    )

    class Meta:
        model = DonorCategoryData
        fields = ('donor', 'category', 'shipped_before', 'shipped_after')


class ItemReportFilter(ReportFilter):
    shipped_before = django_filters.DateFilter(
        lookup_expr='lte',
        name='package__shipment__shipment_date',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped before ' + DATE_INPUT_HELP
    )
    shipped_after = django_filters.DateFilter(
        lookup_expr='gte',
        name='package__shipment__shipment_date',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped after ' + DATE_INPUT_HELP
    )
    partner = django_filters.ModelChoiceFilter(
        name='package__shipment__partner',
        queryset=CtsUser.objects.filter(role=ROLE_PARTNER).order_by('name')
    )
    status = django_filters.MultipleChoiceFilter(
        name='package__status',
        choices=Shipment.SHIPMENT_STATUS_CHOICES,
        widget=CheckboxSelectMultiple,
        label='Package status'
    )

    class Meta:
        model = PackageItemDBView
        fields = ('partner', 'donor', 'item_category', 'status')


class ShipmentReportFilter(ReportFilter):
    shipped_before = django_filters.DateFilter(
        lookup_expr='lte',
        name='shipment_date',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped before ' + DATE_INPUT_HELP
    )
    shipped_after = django_filters.DateFilter(
        lookup_expr='gte',
        name='shipment_date',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped after ' + DATE_INPUT_HELP
    )
    partner = django_filters.ModelChoiceFilter(
        name='partner',
        queryset=CtsUser.objects.filter(role=ROLE_PARTNER).order_by('name')
    )
    status = django_filters.MultipleChoiceFilter(
        choices=Shipment.SHIPMENT_STATUS_CHOICES,
        widget=CheckboxSelectMultiple,
        label="Shipment status",
    )

    class Meta:
        model = ShipmentDBView
        fields = ('partner', 'status')


class ReceivedItemsByShipmentReportFilter(ReportFilter):
    shipped_before = django_filters.DateFilter(
        lookup_expr='lte',
        name='shipment_date',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped before ' + DATE_INPUT_HELP
    )
    shipped_after = django_filters.DateFilter(
        lookup_expr='gte',
        name='shipment_date',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped after ' + DATE_INPUT_HELP
    )

    class Meta:
        model = ShipmentDBView
        fields = ()


class ReceivedItemsByDonorOrPartnerReportFilter(ReportFilter):
    shipped_before = django_filters.DateFilter(
        lookup_expr='lte',
        name='shipment__shipment_date',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped before ' + DATE_INPUT_HELP
    )
    shipped_after = django_filters.DateFilter(
        lookup_expr='gte',
        name='shipment__shipment_date',
        # D/M/Y is typical in Jordan, so use that
        input_formats=DATE_INPUT_FORMATS,
        label='Shipped after ' + DATE_INPUT_HELP
    )
    partner = django_filters.ModelChoiceFilter(
        name='shipment__partner',
        queryset=CtsUser.objects.filter(role=ROLE_PARTNER).order_by('name')
    )

    class Meta:
        model = DonorShipmentData
        fields = ('partner', 'donor')


class ShipmentMonthlySummaryReportFilter(ReportFilter):

    partner = django_filters.ModelChoiceFilter(
        name='partner',
        queryset=CtsUser.objects.filter(role=ROLE_PARTNER).order_by('name')
    )

    class Meta:
        model = ShipmentDBView
        fields = ('partner', )
