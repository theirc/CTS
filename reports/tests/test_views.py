from StringIO import StringIO
from datetime import date, timedelta
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.test import TestCase
from django_tables2_reports.utils import DEFAULT_PARAM_PREFIX
from accounts.models import CtsUser

from accounts.tests.factories import CtsUserFactory, PartnerFactory
from accounts.utils import bootstrap_permissions
from catalog.models import ItemCategory, Donor, CatalogItem
from catalog.tests.factories import DonorFactory, ItemCategoryFactory
from reports.views import PackageReport, DonorByShipmentReport, DonorByCategoryReport, ItemReport, \
    ShipmentReport, ReportBase, ReceivedItemsByShipmentReport, ReceivedItemsByDonorOrPartnerReport, \
    ShipmentMonthlySummaryReport
from shipments.models import Shipment, PackageItem, Package
from shipments.tests.factories import ShipmentFactory, PackageFactory, PackageItemFactory


class TestReportList(TestCase):
    url_name = 'reports_list'
    template_name = 'reports/reports_list.html'

    def setUp(self):
        # super(TestReportList, self).setUp()
        self.user = CtsUserFactory(email="sam@example.com")
        self.user.set_password("password")
        self.user.save()
        assert self.client.login(email="sam@example.com", password="password")

    def get_expected_reports(self):
        """Update this list each time a report is added or removed."""
        return [
            PackageReport,
            DonorByShipmentReport,
            DonorByCategoryReport,
            ItemReport,
            ShipmentReport,
            ReceivedItemsByShipmentReport,
            ReceivedItemsByDonorOrPartnerReport,
            ShipmentMonthlySummaryReport,
            # add new reports above the test report
            BadReportClassForTesting,
        ]

    def test_unauthenticated(self):
        """View requires authentication."""
        self.client.logout()
        response = self.client.get(reverse(self.url_name))
        self.assertEqual(response.status_code, 302)

    def test_expected_reports(self):
        """Basic check that the correct reports are returned."""
        response = self.client.get(reverse(self.url_name))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)
        self.assertTrue('reports' in response.context)
        expected = self.get_expected_reports()
        actual = response.context['reports']
        self.assertEqual([c.__name__ for c in actual],
                         [c.__name__ for c in expected])


class ReportTestMixin(object):
    report_class = None
    template_name = 'reports/report.html'

    important_date = date(1972, 11, 3)
    day_before = date(1972, 11, 2)
    day_after = date(1972, 11, 4)

    def setUp(self):
        super(ReportTestMixin, self).setUp()
        self.user = CtsUserFactory(email="sam@example.com")
        self.user.set_password("password")
        self.user.save()
        assert self.client.login(email="sam@example.com", password="password")
        self.url = reverse(self.report_class.get_report_url_name())

    @classmethod
    def setUpClass(cls):
        super(ReportTestMixin, cls).setUpClass()
        bootstrap_permissions()

        cls.partner1 = PartnerFactory()
        cls.partner2 = PartnerFactory()
        cls.partner3 = PartnerFactory()

        cls.donor1 = DonorFactory()
        cls.donor2 = DonorFactory()
        cls.donor3 = DonorFactory()

        cls.category1 = ItemCategoryFactory()
        cls.category2 = ItemCategoryFactory()
        cls.category3 = ItemCategoryFactory()

        cls.shipment1 = ShipmentFactory(partner=cls.partner1,
                                        shipment_date=cls.day_before,
                                        status=Shipment.STATUS_IN_TRANSIT)

        cls.package1 = PackageFactory(shipment=cls.shipment1,
                                      status=Shipment.STATUS_IN_TRANSIT)
        cls.item1 = PackageItemFactory(package=cls.package1, donor=cls.donor1,
                                       item_category=cls.category1)

        cls.shipment2 = ShipmentFactory(partner=cls.partner2,
                                        shipment_date=cls.important_date,
                                        status=Shipment.STATUS_RECEIVED)
        cls.package2 = PackageFactory(shipment=cls.shipment2,
                                      status=Shipment.STATUS_RECEIVED)
        cls.item2 = PackageItemFactory(package=cls.package2, donor=cls.donor2,
                                       item_category=cls.category2)

        cls.shipment3 = ShipmentFactory(partner=cls.partner3,
                                        shipment_date=cls.day_after,
                                        status=Shipment.STATUS_CANCELED)
        cls.package3 = PackageFactory(shipment=cls.shipment3,
                                      status=Shipment.STATUS_CANCELED)
        cls.item3 = PackageItemFactory(package=cls.package3, donor=cls.donor3,
                                       item_category=cls.category3)

    @classmethod
    def tearDownClass(cls):
        super(ReportTestMixin, cls).tearDownClass()
        PackageItem.objects.all().delete()
        CatalogItem.objects.all().delete()
        Package.objects.all().delete()
        Shipment.objects.all().delete()
        CtsUser.objects.all().delete()
        ItemCategory.objects.all().delete()
        Donor.objects.all().delete()

    def ajax_get(self, *args, **kwargs):
        """Like self.client.get, but looks like it came via ajax"""
        kwargs['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        return self.client.get(*args, **kwargs)

    def csv_get(self, url, *args, **kwargs):
        """Like self.client.get, but asks for response as CSV"""
        parm_name = "%s-%s" % (DEFAULT_PARAM_PREFIX,
                               self.report_class.table_class.__name__.lower())
        if "?" in url:
            url = url + "&" + parm_name + "=csv"
        else:
            url = url + "?" + parm_name + "=csv"
        return self.client.get(url, *args, **kwargs)

    def test_200(self):
        rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, self.template_name)

    def test_ajax_200(self):
        rsp = self.ajax_get(self.url)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(rsp, self.ajax_template_name)

    def test_report_title(self):
        self.assertEqual(self.expected_report_title, self.report_class.get_report_title())

    def test_csv_200(self):
        rsp = self.csv_get(self.url)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp['content-type'], 'text/csv; charset=utf-8')


class PackageReportTest(ReportTestMixin, TestCase):
    report_class = PackageReport
    ajax_template_name = 'reports/ajax_package.html'
    expected_report_title = 'Package Report'

    def test_get_queryset(self):
        view = self.report_class()
        qs = view.get_queryset()
        self.assertEqual(3, qs.count())
        # The queryset actually contains PackageDBView objects, so compare
        # by pks
        pks = [o.pk for o in qs]
        self.assertIn(self.package1.pk, pks)
        self.assertIn(self.package2.pk, pks)

    def test_get_table(self):
        rsp = self.ajax_get(self.url)
        self.assertContains(rsp, "<table")

    def test_csv_table(self):
        rsp = self.csv_get(self.url)
        body = rsp.content.decode('utf-8')
        lines = StringIO(body).readlines()
        self.assertEqual(4, len(lines))

    def test_partner_filtering(self):
        rsp = self.ajax_get(self.url + "?partner=%d" % self.partner1.pk)
        self.assertContains(rsp, "<table")
        qs = rsp.context['queryset']
        pks = [o.pk for o in qs]
        self.assertIn(self.package1.pk, pks)
        self.assertNotIn(self.package2.pk, pks)

    def test_partner_limits_shipment_choices(self):
        # provide a partner in the filters
        # limits the list of available shipments
        rsp = self.client.get(self.url + "?partner=%d" % self.partner1.pk)
        shipments = rsp.context['filter'].form['shipment'].field.choices
        # First choice is "----", 2nd is the shipment for this partner
        self.assertEqual(2, len(shipments))

    def test_status_filtering(self):
        rsp = self.ajax_get(self.url + "?status=%d" % Shipment.STATUS_RECEIVED)
        qs = rsp.context['queryset']
        pks = [o.pk for o in qs]
        self.assertNotIn(self.package1.pk, pks)
        self.assertIn(self.package2.pk, pks)

    def test_shipment_filtering(self):
        rsp = self.ajax_get(self.url + "?shipment=%d" % self.shipment1.pk)
        qs = rsp.context['queryset']
        pks = [o.pk for o in qs]
        self.assertIn(self.package1.pk, pks)
        self.assertNotIn(self.package2.pk, pks)


class DonorByShipmentReportTest(ReportTestMixin, TestCase):
    """
    Note: PackageItems have donors; packages and shipments do not, but reflect
    the donors in their package items.
    """
    report_class = DonorByShipmentReport
    ajax_template_name = 'reports/donor_by_shipment_table.html'
    expected_report_title = 'Donor By Shipment Report'

    def test_get_queryset(self):
        # Without filtering, should see an entry for each donor who has shipments
        view = self.report_class()
        qs = view.get_queryset()
        self.assertEqual(3, qs.count())
        self.assertEqual(set([self.donor1.pk, self.donor2.pk, self.donor3.pk]),
                         set([line.donor.pk for line in qs]))

    def test_donor_filtering(self):
        rsp = self.ajax_get(self.url + "?donor=%d" % self.donor2.pk)
        qs = rsp.context['queryset']
        # Should see one donor
        self.assertEqual(1, qs.count())
        line = qs[0]
        self.assertEqual(self.donor2, line.donor)

    def test_partner_filtering(self):
        # Should only list donors who have provided shipments to the specified partner.
        rsp = self.ajax_get(self.url + "?partner=%d" % self.partner1.pk)
        qs = rsp.context['queryset']
        # Should see one donor
        self.assertEqual(1, qs.count())
        line = qs[0]
        self.assertEqual(self.donor1, line.donor)

    def test_shipped_before_filtering(self):
        # Should only list donors who have shipments shipped on or before the specified date
        rsp = self.ajax_get(self.url +
                            "?shipped_before=%s" % self.important_date.strftime("%m/%d/%Y"))
        qs = rsp.context['queryset']
        # Should see two donors
        self.assertEqual(2, qs.count())
        pks = set([line.donor.pk for line in qs])
        self.assertEqual(set([self.donor1.pk, self.donor2.pk]), pks)

    def test_shipped_after_filtering(self):
        # Should only list donors who have shipments shipped on or before the specified date
        rsp = self.ajax_get(self.url +
                            "?shipped_after=%s" % self.important_date.strftime("%m/%d/%Y"))
        qs = rsp.context['queryset']
        # Should see two donors
        self.assertEqual(2, qs.count())
        pks = set([line.donor.pk for line in qs])
        self.assertEqual(set([self.donor2.pk, self.donor3.pk]), pks)

    def test_status_filtering(self):
        # Should only list donors who have shipments with the specified status
        rsp = self.ajax_get(self.url + "?status=%d" % Shipment.STATUS_IN_TRANSIT)
        qs = rsp.context['queryset']
        # Should see one donor
        self.assertEqual(1, qs.count())
        line = qs[0]
        self.assertEqual(self.donor1, line.donor)


class DonorByCategoryReportTest(ReportTestMixin, TestCase):
    report_class = DonorByCategoryReport
    ajax_template_name = 'reports/donor_by_category_table.html'
    expected_report_title = 'Donor By Category Report'

    def test_get_queryset(self):
        # Without filtering, should see an entry for each donor who has shipments
        view = self.report_class()
        qs = view.get_queryset()
        # Should see one donor
        self.assertEqual(3, qs.count())
        self.assertEqual(set([self.donor1.pk, self.donor2.pk, self.donor3.pk]),
                         set([line.donor.pk for line in qs]))

    def test_donor_filtering(self):
        rsp = self.ajax_get(self.url + "?donor=%d" % self.donor2.pk)
        qs = rsp.context['queryset']
        # Should see one donor
        self.assertEqual(1, qs.count())
        line = qs[0]
        self.assertEqual(self.donor2, line.donor)

    def test_shipped_before_filtering(self):
        # Should only list donors who have shipments shipped before the specified date
        rsp = self.ajax_get(self.url +
                            "?shipped_before=%s" % self.important_date.strftime("%m/%d/%Y"))
        qs = rsp.context['queryset']
        # Should see two donors
        self.assertEqual(2, qs.count())
        pks = set([line.donor.pk for line in qs])
        self.assertEqual(set([self.donor1.pk, self.donor2.pk]), pks)

    def test_shipped_after_filtering(self):
        # Should only list donors who have shipments shipped before the specified date
        rsp = self.ajax_get(self.url +
                            "?shipped_after=%s" % self.important_date.strftime("%m/%d/%Y"))
        qs = rsp.context['queryset']
        # Should see two donors
        self.assertEqual(2, qs.count())
        pks = set([line.donor.pk for line in qs])
        self.assertEqual(set([self.donor2.pk, self.donor3.pk]), pks)

    def test_category_filtering(self):
        rsp = self.ajax_get(self.url + "?category=%d" % self.category1.pk)
        qs = rsp.context['queryset']
        # Should see one donor
        self.assertEqual(1, qs.count())
        line = qs[0]
        self.assertEqual(self.donor1, line.donor)


class ItemReportTest(ReportTestMixin, TestCase):
    report_class = ItemReport
    ajax_template_name = 'reports/ajax_item.html'
    expected_report_title = 'Item Report'

    # filters: shipped_before, shipped_after, partner, status, donor, category
    def test_get_queryset(self):
        view = self.report_class()
        qs = view.get_queryset()
        self.assertEqual(3, len(qs))

    def test_partner_filter(self):
        rsp = self.ajax_get(self.url + "?partner=%d" % self.partner1.pk)
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertIn(self.item1.pk, pks)
        self.assertNotIn(self.item2.pk, pks)

    def test_donor_filter(self):
        rsp = self.ajax_get(self.url + "?donor=%d" % self.donor1.pk)
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertIn(self.item1.pk, pks)
        self.assertNotIn(self.item2.pk, pks)

    def test_category_filtering(self):
        rsp = self.ajax_get(self.url + "?item_category=%d" % self.category1.pk)
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertIn(self.item1.pk, pks)
        self.assertNotIn(self.item2.pk, pks)

    def test_shipped_before_filter(self):
        # Should only list package items from shipments shipped before the date
        rsp = self.ajax_get(self.url +
                            "?shipped_before=%s" % self.important_date.strftime('%m/%d/%Y'))
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertIn(self.item1.pk, pks)
        self.assertIn(self.item2.pk, pks)
        self.assertNotIn(self.item3.pk, pks)

    def test_shipped_after_filter(self):
        # Should only list package items from shipments shipped before the date
        rsp = self.ajax_get(self.url +
                            "?shipped_after=%s" % self.important_date.strftime('%m/%d/%Y'))
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertNotIn(self.item1.pk, pks)
        self.assertIn(self.item2.pk, pks)
        self.assertIn(self.item3.pk, pks)

    def test_status_filtering(self):
        # Should only list items from packages with the specified status
        rsp = self.ajax_get(self.url + "?status=%d" % Shipment.STATUS_IN_TRANSIT)
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertIn(self.item1.pk, pks)
        self.assertNotIn(self.item2.pk, pks)

    def test_statuses_filtering(self):
        # Should only list items from packages with the specified statuses
        rsp = self.ajax_get(self.url + "?status=%d&status=%d" % (Shipment.STATUS_IN_TRANSIT,
                                                                 Shipment.STATUS_RECEIVED))
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertIn(self.item1.pk, pks)
        self.assertIn(self.item2.pk, pks)
        self.assertNotIn(self.item3.pk, pks)


class ShipmentReportTest(ReportTestMixin, TestCase):
    report_class = ShipmentReport
    expected_report_title = "Shipment Report"
    ajax_template_name = "reports/ajax_report.html"
    # filters: partner, status, shipped_before, shipped_after

    def test_get_queryset(self):
        view = self.report_class()
        qs = view.get_queryset()
        self.assertEqual(3, len(qs))

    def test_partner_filter(self):
        rsp = self.ajax_get(self.url + "?partner=%d" % self.partner1.pk)
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertIn(self.shipment1.pk, pks)
        self.assertNotIn(self.shipment2.pk, pks)

    def test_status_filter(self):
        # shipments with given status
        rsp = self.ajax_get(self.url + "?status=%d" % Shipment.STATUS_IN_TRANSIT)
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertIn(self.shipment1.pk, pks)
        self.assertNotIn(self.shipment2.pk, pks)


class ReceivedItemsByShipmentReportTest(ReportTestMixin, TestCase):
    report_class = ReceivedItemsByShipmentReport
    expected_report_title = "Received Items By Shipment Report"
    ajax_template_name = "reports/ajax_report.html"
    # filters: hipped_before, shipped_after

    def test_get_queryset(self):
        view = self.report_class()
        qs = view.get_queryset()
        self.assertEqual(1, len(qs))

    def test_shipped_before_filter(self):
        # Should only list shipments shipped before the date
        rsp = self.ajax_get(self.url +
                            "?shipped_before=%s" % self.day_after.strftime('%m/%d/%Y'))
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertIn(self.shipment2.pk, pks)
        rsp = self.ajax_get(self.url +
                            "?shipped_before=%s" % self.day_before.strftime('%m/%d/%Y'))
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertNotIn(self.shipment2.pk, pks)

    def test_shipped_after_filter(self):
        # Should only list shipments shipped after the date
        rsp = self.ajax_get(self.url +
                            "?shipped_after=%s" % self.day_before.strftime('%m/%d/%Y'))
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertIn(self.shipment2.pk, pks)
        rsp = self.ajax_get(self.url +
                            "?shipped_after=%s" % self.day_after.strftime('%m/%d/%Y'))
        qs = rsp.context['queryset']
        pks = [item.pk for item in qs]
        self.assertNotIn(self.shipment2.pk, pks)


class ReceivedItemsByDonorOrPartnerReportTest(ReportTestMixin, TestCase):
    report_class = ReceivedItemsByDonorOrPartnerReport
    ajax_template_name = "reports/ajax_report.html"
    expected_report_title = 'Received Items By Donor Or Partner Report'

    # filters: hipped_before, shipped_after, donor, partner,

    def test_get_queryset(self):
        # Without filtering, should see an entry for each donor who has shipments
        # marked as received
        view = self.report_class()
        qs = view.get_queryset()
        # Should see one donor
        self.assertEqual(1, qs.count())
        self.assertEqual(set([self.donor2.pk]),
                         set([line.donor.pk for line in qs]))

    def test_donor_filtering(self):
        rsp = self.ajax_get(self.url + "?donor=%d" % self.donor2.pk)
        qs = rsp.context['queryset']
        # Should see one donor
        self.assertEqual(1, qs.count())
        line = qs[0]
        self.assertEqual(self.donor2, line.donor)
        rsp = self.ajax_get(self.url + "?donor=%d" % self.donor1.pk)
        qs = rsp.context['queryset']
        # Should see one donor
        self.assertEqual(0, qs.count())

    def test_partner_filter(self):
        rsp = self.ajax_get(self.url + "?partner=%d" % self.partner2.pk)
        qs = rsp.context['queryset']
        partner_pks = [item.shipment.partner.pk for item in qs]
        self.assertIn(self.partner2.pk, partner_pks)
        self.assertNotIn(self.partner1.pk, partner_pks)

    def test_shipped_before_filtering(self):
        # Should only list donors who have shipments shipped & received before the specified date
        rsp = self.ajax_get(self.url +
                            "?shipped_before=%s" % self.important_date.strftime("%m/%d/%Y"))
        qs = rsp.context['queryset']
        # Should see one donors
        self.assertEqual(1, qs.count())
        pks = set([line.donor.pk for line in qs])
        self.assertEqual(set([self.donor2.pk]), pks)

    def test_shipped_after_filtering(self):
        # Should only list donors who have shipments shipped & received after the specified date
        rsp = self.ajax_get(self.url +
                            "?shipped_after=%s" % self.important_date.strftime("%m/%d/%Y"))
        qs = rsp.context['queryset']
        # Should see one donors
        self.assertEqual(1, qs.count())
        pks = set([line.donor.pk for line in qs])
        self.assertEqual(set([self.donor2.pk]), pks)


class ShipmentMonthlySummaryReportTest(ReportTestMixin, TestCase):
    report_class = ShipmentMonthlySummaryReport
    expected_report_title = "Shipment Monthly Summary Report"
    ajax_template_name = "reports/ajax_report.html"
    # filters: Partner!

    def test_partner_filter(self):
        rsp = self.ajax_get(self.url + "?partner=%d" % self.partner1.pk)
        qs = rsp.context['queryset']
        self.assertEqual(1, len(qs))
        self.assertEqual(self.day_before.month, qs[0]['month'].month)
        self.assertEqual(1, qs[0]['pk__count'])
        last_month = self.day_before - timedelta(days=30)
        ShipmentFactory(
            partner=self.partner1,
            shipment_date=last_month,
            status=Shipment.STATUS_IN_TRANSIT)
        rsp = self.ajax_get(self.url + "?partner=%d" % self.partner1.pk)
        qs = rsp.context['queryset']
        # 2 records
        self.assertEqual(2, len(qs))
        self.assertEqual(last_month.month, qs[1]['month'].month)
        self.assertEqual(1, qs[1]['pk__count'])

    def test_get_queryset(self):
        view = self.report_class()
        qs = view.get_queryset()
        # all shipped within same month
        self.assertEqual(1, len(qs))
        self.assertEqual(self.day_before.month, qs[0]['month'].month)
        self.assertEqual(3, qs[0]['pk__count'])

        last_month = self.day_before - timedelta(days=30)
        ShipmentFactory(
            partner=self.partner1,
            shipment_date=last_month,
            status=Shipment.STATUS_IN_TRANSIT)
        qs = view.get_queryset()
        # 2 records
        self.assertEqual(2, len(qs))
        self.assertEqual(last_month.month, qs[1]['month'].month)
        self.assertEqual(1, qs[1]['pk__count'])


class BadReportClassForTesting(ReportBase):
    pass


class TestBadReportClass(TestCase):
    def test_no_filter(self):
        view = BadReportClassForTesting()
        with self.assertRaises(ImproperlyConfigured):
            view.get_filter()

    def test_no_queryset(self):
        view = BadReportClassForTesting()
        with self.assertRaises(NotImplementedError):
            view.get_queryset()

    def test_no_table_class(self):
        view = BadReportClassForTesting()
        with self.assertRaises(ImproperlyConfigured):
            view.get_table(None)
