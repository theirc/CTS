from django.test import TestCase

from accounts.utils import bootstrap_permissions
from accounts.models import ROLE_PARTNER, ROLE_MANAGER
from accounts.tests.factories import CtsUserFactory
from catalog.tests.factories import DonorFactory
from reports.filters import PackageReportFilter, DonorByShipmentReportFilter, \
    DonorByCategoryReportFilter, ItemReportFilter, ShipmentReportFilter
from reports.tests.factories import DonorShipmentDataFactory, DonorCategoryDataFactory
from shipments.tests.factories import ShipmentFactory, PackageFactory, PackageItemFactory


class ReportFilterMixin(object):
    """Tests that are common to all our filter classes"""
    filter_class = None  # Subclasses set this
    partner_filtering = True   # Most filters do partner filtering

    @classmethod
    def setUpClass(cls):
        bootstrap_permissions()

    def setUp(self):
        self.partner = CtsUserFactory(role=ROLE_PARTNER)

    def item_for_partner(self, user):
        """Return a test object that is associated with the given user as partner,
        if that makes sense for the kinds of objects being filtered by this filter."""
        raise NotImplementedError("Users of ReportFilterMixin must implement item_for_partner()")

    def can_see_other_partners_records(self, user):
        """Return True if the user can see other partners' records"""

        other_partner = CtsUserFactory(role=ROLE_PARTNER)
        item = self.item_for_partner(other_partner)
        queryset = self.filter_class._meta.model.objects.all()
        filter = self.filter_class(data={}, queryset=queryset, user=user)
        pks = filter.qs.values_list('pk', flat=True)
        return item.id in pks

    def test_no_privs(self):
        """If user has no privs, we filter out items from other partners"""
        if not self.partner_filtering:
            return
        self.assertFalse(self.can_see_other_partners_records(self.partner))

    def test_privs(self):
        """If user has privs, we do not filter out items from other partners"""
        if not self.partner_filtering:
            return
        priv_user = CtsUserFactory(role=ROLE_MANAGER)
        self.assertTrue(self.can_see_other_partners_records(priv_user))

    def test_superuser(self):
        """If user has no privs but is superuser, we do not filter out items from other partners"""
        if not self.partner_filtering:
            return
        superuser = CtsUserFactory(role=ROLE_PARTNER, is_superuser=True)
        self.assertTrue(self.can_see_other_partners_records(superuser))

    def test_partner_filtering(self):
        """Users can filter by partner"""
        if not self.partner_filtering:
            return

        # We can't tell if its working unless they have permission to see
        # other users' records
        user = CtsUserFactory(role=ROLE_MANAGER)
        partner1 = self.partner
        partner2 = CtsUserFactory(role=ROLE_PARTNER)

        partner1_item = self.item_for_partner(partner1)
        partner2_item = self.item_for_partner(partner2)

        queryset = self.filter_class._meta.model.objects.all()

        # Filter to only partner1 items
        data = {'partner': partner1.pk}
        filter = self.filter_class(data=data, queryset=queryset, user=user)

        pks = filter.qs.values_list('pk', flat=True)
        self.assertIn(partner1_item.id, pks)
        self.assertNotIn(partner2_item.id, pks)

        # Filter to only partner2 items
        data = {'partner': partner2.pk}
        filter = self.filter_class(data=data, queryset=queryset, user=user)

        pks = filter.qs.values_list('pk', flat=True)
        self.assertNotIn(partner1_item.id, pks)
        self.assertIn(partner2_item.id, pks)


class DonorFilterTestMixin(object):
    """Tests for filters that can filter on donors"""
    def test_donor_filtering(self):
        donor1 = DonorFactory()
        donor2 = DonorFactory()
        item1 = self.item_for_donor(donor1)
        item2 = self.item_for_donor(donor2)
        queryset = self.filter_class._meta.model.objects.all()
        filter = self.filter_class(data={'donor': donor1.pk}, queryset=queryset, user=self.partner)
        pks = filter.qs.values_list('pk', flat=True)
        self.assertIn(item1.pk, pks)
        self.assertNotIn(item2.pk, pks)

    def item_for_donor(self, donor):
        item = self.item_for_partner(self.partner)
        item.donor = donor
        item.save()
        return item


class PackageReportFilterTest(ReportFilterMixin, TestCase):
    filter_class = PackageReportFilter

    def item_for_partner(self, user):
        return PackageFactory(shipment=ShipmentFactory(partner=user))


class DonorByShipmentReportFilterTest(ReportFilterMixin, DonorFilterTestMixin, TestCase):
    filter_class = DonorByShipmentReportFilter

    def item_for_partner(self, user):
        item = DonorShipmentDataFactory()
        item.shipment.partner = user
        item.shipment.save()
        return item


class DonorByCategoryReportFilterTest(ReportFilterMixin, DonorFilterTestMixin, TestCase):
    filter_class = DonorByCategoryReportFilter
    partner_filtering = False

    def item_for_donor(self, donor):
        return DonorCategoryDataFactory(donor=donor)


class ItemReportFilterTest(ReportFilterMixin, DonorFilterTestMixin, TestCase):
    filter_class = ItemReportFilter

    def item_for_partner(self, user):
        item = PackageItemFactory()
        item.package.shipment.partner = user
        item.package.shipment.save()
        return item


class ShipmentReportFilterTest(ReportFilterMixin, TestCase):
    filter_class = ShipmentReportFilter

    def item_for_partner(self, user):
        return ShipmentFactory(partner=user)
