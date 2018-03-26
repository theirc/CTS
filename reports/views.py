from braces.views import LoginRequiredMixin, AjaxResponseMixin
from django.conf import settings
from django_tables2_reports.config import RequestConfigReport as RequestConfig
from django_tables2_reports.utils import DEFAULT_PARAM_PREFIX, create_report_http_response, \
    REPORT_CONTENT_TYPES

from django.conf.urls import url
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db import connection
from django.db.models import Count
from django.shortcuts import render
from django.views.generic import TemplateView

from accounts.models import ROLE_PARTNER
from cts.utils import camel_to_space, camel_to_underscore, not_falsey

from shipments.models import PackageDBView, ShipmentDBView, PackageItemDBView, Shipment

from . import filters
from . import tables
from .models import DonorCategoryData, DonorShipmentData


# Flag our CSV downloads with the encoding that django-tables2-reports uses for them
REPORT_CONTENT_TYPES['csv'] = 'text/csv; charset=%s' % settings.DEFAULT_CHARSET


class ReportList(LoginRequiredMixin, TemplateView):
    template_name = 'reports/reports_list.html'

    def get_context_data(self, **kwargs):
        """Order is determined by the order Report classes are defined in."""
        kwargs['reports'] = ReportBase.__subclasses__()
        return super(ReportList, self).get_context_data(**kwargs)


class ReportBase(LoginRequiredMixin, AjaxResponseMixin, TemplateView):
    filter_class = None
    table_class = None
    partners_may_access = True

    # Default options for the report table.
    default_page_size = 1000
    empty_text = "There are no items to display."
    attrs = {'class': 'table table-hover table-bordered'}

    # A report can override these, but they will be derived from the class
    # name by default.
    report_title = ''
    report_url_name = ''
    template_name = ''
    ajax_template_name = ''
    url_pattern = ''

    @classmethod
    def user_may_access(cls, user):
        return user.is_superuser or user.role != ROLE_PARTNER or cls.partners_may_access

    def dispatch(self, request, *args, **kwargs):
        if not self.user_may_access(request.user):
            raise PermissionDenied  # return a forbidden response
        return super(ReportBase, self).dispatch(
            request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        param_report = "%s-%s" % (DEFAULT_PARAM_PREFIX, self.table_class.__name__.lower())
        if self.request.GET.get(param_report, ''):
            # create the table; middleware will generate the CSV response
            queryset = self.get_filter().qs
            table = self.get_table(queryset, downloadable=True)
            table.param_report = param_report
            return create_report_http_response(table, request)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_ajax(self, request, *args, **kwargs):
        """Load the report table via AJAX after the initial page load."""
        context = self.get_ajax_context_data()
        return render(request, self.get_ajax_template_names(), context)

    def get_ajax_context_data(self, **kwargs):
        queryset = self.get_filter().qs
        report = self.get_table(queryset)
        context = {
            'queryset': queryset,
            'report': report,
        }
        context.update(**kwargs)
        return context

    def get_ajax_template_names(self):
        """
        To use a custom template, create a template in `reports` with this
        report's name prefixed by 'ajax_'.
        """
        name = self.__class__.get_report_url_name()
        return not_falsey([self.ajax_template_name, 'reports/ajax_{}.html'.format(name),
                             'reports/ajax_report.html'])

    def get_context_data(self, **kwargs):
        kwargs['filter'] = self.get_filter()
        return super(ReportBase, self).get_context_data(**kwargs)

    def get_filter(self):
        """Allow filtering of the queryset using django-filter."""
        if not getattr(self, 'filter_class', None):
            raise ImproperlyConfigured("Report class must define `filter_class`")
        queryset = self.get_queryset()
        return self.filter_class(data=self.request.GET, queryset=queryset, user=self.request.user)

    def get_queryset(self):
        """The base queryset that defines this report.

        The user can use a filter against this queryset to narrow results.
        """
        raise NotImplementedError("Report class must implement `get_queryset`.")

    def get_table(self, queryset, downloadable=False):
        """Convert the queryset to a report table."""
        if not getattr(self, 'table_class', None):
            raise ImproperlyConfigured("Report class must define `table_class`")
        data = self.get_table_data(queryset)
        if downloadable:
            downloadable_class = getattr(self, 'downloadable_table_class', self.table_class)
            table = downloadable_class(
                data, empty_text=self.empty_text, attrs=self.attrs
            )
        else:
            table = self.table_class(data, empty_text=self.empty_text, attrs=self.attrs)

        config = RequestConfig(self.request, paginate={
            'per_page': self.page_size,
        })
        config.configure(table)
        return table

    def get_table_data(self, queryset):
        """Additional processing before converting the queryset to a table."""
        return queryset

    @classmethod
    def get_report_title(cls):
        """The title of this report.

        Derives from the class name by default; override method if desired.
        """
        return camel_to_space(cls.__name__).title()

    @classmethod
    def get_report_url_name(cls):
        """The name that can be reversed to get the URL for this report.

        Derives from the class name by default; override method if desired.
        """
        return camel_to_underscore(cls.__name__.replace('Report', '')).lower()

    def get_template_names(self):
        """
        To use a custom template, create a template in `reports` with this
        report's name.
        """
        name = self.__class__.get_report_url_name()
        return not_falsey([self.template_name, 'reports/{}.html'.format(name), 'reports/report.html'])

    @classmethod
    def get_url_pattern(cls):
        """Derive the url pattern and name from this class's name."""
        name = cls.get_report_url_name()
        url_pattern = cls.url_pattern or r'^%s/$' % name
        return url(url_pattern, cls.as_view(), name=name)

    @property
    def page_size(self):
        return self.request.GET.get('page_size', self.default_page_size)


class PackageReport(ReportBase):
    filter_class = filters.PackageReportFilter
    table_class = tables.PackageReportTable
    downloadable_table_class = tables.PackageDownloadableTable
    template_name = 'reports/report_package.html'
    partners_may_access = True

    def get_queryset(self):
        order_by = ('shipment__partner', '-shipment__shipment_date',
                    'shipment__description', 'number_in_shipment')
        packages = PackageDBView.objects.order_by(*order_by)
        packages = packages.prefetch_related(
            'shipment', 'shipment__partner', 'last_scan')
        return packages

    def get_ajax_context_data(self, **kwargs):
        context = super(PackageReport, self).get_ajax_context_data(**kwargs)
        context.update(context['report'].get_table_footer(context['queryset']))
        return context


class DonorByShipmentReport(ReportBase):
    filter_class = filters.DonorByShipmentReportFilter
    table_class = tables.DonorByShipmentReportTable
    downloadable_table_class = tables.DonorByShipmentDownloadableTable
    partners_may_access = True

    def get_queryset(self):
        order_by = ('shipment__partner', 'donor__name', 'donor',
                    'shipment__shipment_date', 'shipment')
        data = DonorShipmentData.objects.order_by(*order_by)
        data = data.prefetch_related('donor', 'shipment')
        return data

    def get_ajax_context_data(self, **kwargs):
        context = super(DonorByShipmentReport, self).get_ajax_context_data(**kwargs)
        context.update(context['report'].get_table_footer(context['queryset']))
        return context


class DonorByCategoryReport(ReportBase):
    filter_class = filters.DonorByCategoryReportFilter
    table_class = tables.DonorByCategoryReportTable
    partners_may_access = False
    downloadable_table_class = tables.DonorByCategoryDownloadableTable

    def get_queryset(self):
        order_by = ('donor__name', 'donor', 'category__name', 'category')
        data = DonorCategoryData.objects.order_by(*order_by)
        data = data.prefetch_related('donor', 'category')
        return data

    def get_ajax_context_data(self, **kwargs):
        context = super(DonorByCategoryReport, self).get_ajax_context_data(**kwargs)
        context.update(context['report'].get_table_footer(context['queryset']))
        return context


class ItemReport(ReportBase):
    filter_class = filters.ItemReportFilter
    table_class = tables.ItemReportTable
    downloadable_table_class = tables.ItemDownloadableTable
    partners_may_access = False

    def get_queryset(self):
        order_by = ('package__shipment__shipment_date', 'package__shipment')
        items = PackageItemDBView.objects.order_by(*order_by)
        items = items.prefetch_related(
            'package', 'item_category', 'donor', 'package__shipment__partner')
        return items

    def get_ajax_context_data(self, **kwargs):
        context = super(ItemReport, self).get_ajax_context_data(**kwargs)
        context.update(context['report'].get_table_footer(context['queryset']))
        return context


class ShipmentReport(ReportBase):
    filter_class = filters.ShipmentReportFilter
    table_class = tables.ShipmentReportTable
    partners_may_access = True

    def get_queryset(self):
        order_by = ('partner__name', 'shipment_date', 'description')
        shipments = ShipmentDBView.objects.order_by(*order_by)
        shipments = shipments.prefetch_related('partner')
        return shipments


class ReceivedItemsByShipmentReport(ReportBase):
    filter_class = filters.ReceivedItemsByShipmentReportFilter
    table_class = tables.ReceivedItemsByShipmentReportTable
    partners_may_access = False

    def get_queryset(self):
        order_by = ('-shipment_date', 'description')
        shipments = ShipmentDBView.objects.filter(
            status=Shipment.STATUS_RECEIVED
        ).order_by(*order_by)
        return shipments


class ReceivedItemsByDonorOrPartnerReport(ReportBase):
    filter_class = filters.ReceivedItemsByDonorOrPartnerReportFilter
    table_class = tables.ReceivedItemsByDonorOrPartnerReportTable
    partners_may_access = False

    def get_queryset(self):
        order_by = ('-shipment__shipment_date', 'shipment__partner', 'donor__name',
                    'donor', 'shipment')
        data = DonorShipmentData.objects.filter(
            shipment__status=Shipment.STATUS_RECEIVED
        ).order_by(*order_by)
        data = data.prefetch_related('donor', 'shipment')
        return data


class ShipmentMonthlySummaryReport(ReportBase):
    filter_class = filters.ShipmentMonthlySummaryReportFilter
    table_class = tables.ShipmentMonthlySummaryReportTable
    partners_may_access = False

    def get_queryset(self):
        truncate_date = connection.ops.date_trunc_sql('month', 'shipment_date')
        qs = ShipmentDBView.objects.extra({'month': truncate_date})
        order_by = ('-month', )
        if hasattr(self, 'request') and self.request.GET.get('partner', None):
            data = qs.values('month', 'partner__name').annotate(Count('pk')).order_by(*order_by)
        else:
            data = qs.values('month').annotate(Count('pk')).order_by(*order_by)
        return data
