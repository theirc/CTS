from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator
from django.db import models, transaction, connection
from django.db.models import Q, Sum, Max
from django.utils.timezone import now

from accounts.models import CtsUser, ROLE_PARTNER
from catalog.models import Donor, Supplier, Transporter, DonorCode
from cts.utils import USDCurrencyField
from reports.models import DonorShipmentData


class ShipmentMixin(object):

    def __unicode__(self):
        if not self.description.strip():
            # Set default description
            shipment_date = datetime.strftime(self.shipment_date, "%Y-%m-%d")
            return '-'.join([self.partner.name, self.store_release, shipment_date])
        return self.description

    def get_status_count(self, status):
        """Return number of packages in shipment that have the specified status"""
        return self.packages.filter(status=status).count()

    def may_finalize(self):
        return bool(self.pk) and not self.is_finalized() and not self.is_canceled()

    def may_cancel(self):
        return (bool(self.pk)
                and self.status not in
                (Shipment.STATUS_CANCELED, Shipment.STATUS_LOST, Shipment.STATUS_RECEIVED))

    def is_canceled(self):
        return self.status == Shipment.STATUS_CANCELED

    def has_shipped(self):
        return (bool(self.pk)
                and self.status >= Shipment.STATUS_PICKED_UP)

    def may_reopen(self):
        return (bool(self.pk) and self.is_finalized()
                and not self.is_canceled() and not self.has_shipped())

    def delivery_days(self):
        """Number of days from shipment date to expected delivery date"""
        return (self.date_expected - self.shipment_date).days

    def compute_donor_name(self):
        """
        Each PackageItem can have a different donor. If they all have the same donor,
        return that donor's name. If there's more than one, return "Multiple".
        If there are no package items with donors, return "None".
        :return:
        """
        pkg_items = PackageItem.objects.filter(package__shipment_id=self.pk).exclude(donor=None)
        donors = set(pkg_items.values_list('donor__name', flat=True))
        if len(donors) == 1:
            name = donors.pop()
        elif len(donors) > 1:
            name = "Multiple"
        else:
            name = "None"
        return name

    def is_finalized(self):
        return self.status != Shipment.STATUS_IN_PROGRESS

    def may_lose(self):
        return bool(self.pk) and self.is_finalized() and self.has_shipped() and not self.is_lost()

    def is_lost(self):
        return bool(self.pk) and self.status == Shipment.STATUS_LOST


class Shipment(ShipmentMixin, models.Model):
    STATUS_IN_PROGRESS = 1
    STATUS_READY = 2
    STATUS_PICKED_UP = 3
    STATUS_IN_TRANSIT = 4
    STATUS_RECEIVED = 5
    STATUS_OVERDUE = 6
    STATUS_LOST = 7
    STATUS_CANCELED = 8
    SHIPMENT_STATUS_CHOICES = (
        (STATUS_IN_PROGRESS, 'In progress'),
        (STATUS_READY, 'Ready for pickup'),
        (STATUS_PICKED_UP, 'Picked up'),
        (STATUS_IN_TRANSIT, 'In transit'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_LOST, 'Lost'),
        (STATUS_CANCELED, 'Canceled'),
    )

    description = models.CharField(max_length=255, default='')
    shipment_date = models.DateField(default=date.today)
    store_release = models.CharField(max_length=45, default='')
    date_in_transit = models.DateField(blank=True, null=True)
    date_picked_up = models.DateField(blank=True, null=True)
    date_expected = models.DateField(blank=True, null=True)
    date_received = models.DateField(blank=True, null=True)
    status = models.IntegerField(choices=SHIPMENT_STATUS_CHOICES,
                                 default=STATUS_IN_PROGRESS,
                                 db_index=True)
    transporter = models.ForeignKey(Transporter, blank=True, null=True)
    partner = models.ForeignKey(CtsUser,
                                limit_choices_to={'role': ROLE_PARTNER})
    acceptable = models.BooleanField(default=False, blank=True)
    status_note = models.TextField(blank=True)
    donor = models.CharField(max_length=45, null=True, blank=True)
    last_scan_status_label = models.CharField(max_length=128, blank=True, null=True)

    def finalize(self):
        self.status = Shipment.STATUS_READY
        self.save()
        # Any packages that haven't started changing status yet, move to ready status
        self.packages.filter(Q(status=None) | Q(status=Shipment.STATUS_IN_PROGRESS))\
            .update(status=Shipment.STATUS_READY)

    def cancel(self):
        self.status = Shipment.STATUS_CANCELED
        self.save()

    def reopen(self):
        self.status = Shipment.STATUS_IN_PROGRESS
        self.save()
        # Any packages that haven't started transit yet,
        # change back to ready (actually shouldn't be possible to re-open
        # once packages have started transit, but playing it safe)
        self.packages\
            .filter(status=Shipment.STATUS_READY)\
            .update(status=Shipment.STATUS_IN_PROGRESS)

    def save(self, *args, **kwargs):
        if self.pk:
            self.donor = self.compute_donor_name()
        # If a Shipment Status is set to In Transit or Picked Up; set the associated
        # date field
        if self.date_picked_up is None and self.status == Shipment.STATUS_PICKED_UP:
            self.date_picked_up = now().date()
        if self.date_in_transit is None and self.status == Shipment.STATUS_IN_TRANSIT:
            self.date_in_transit = now().date()
        super(Shipment, self).save(*args, **kwargs)

    def next_package_number_in_shipment(self):
        """Return the next package number that should be assigned to a package
        in this shipment"""
        # Quick n' dirty - return 1 more than the max number already in use
        if self.packages.exists():
            max_number = self.packages.aggregate(max_number=Max('number_in_shipment'))['max_number']
            return 1 + max_number
        return 1

    def fast_delete(self):
        """
        Delete this shipment, and its packages and packageitems and scans, while bypassing the
        background stuff that doesn't matter so much while we're deleting anyway.
        """
        # We'll have to update the report data ourselves later,
        # so make a note of the donor, category combinations:
        donor_categories = set(
            (item.donor_id, item.item_category_id)
            for item in PackageItem.objects.filter(package__shipment=self)
        )

        cursor = connection.cursor()

        # delete package items
        item_pks = PackageItem.objects.filter(package__shipment=self).values_list('pk', flat=True)
        if item_pks:
            item_pks = ','.join(str(pk) for pk in item_pks)
            cursor.execute("DELETE FROM shipments_packageitem WHERE id IN (%s)" % item_pks)

        # delete packages
        package_pks = Package.objects.filter(shipment=self).values_list('pk', flat=True)
        if package_pks:
            # Remove any references to scans
            Package.objects.filter(pk__in=package_pks).exclude(last_scan=None)\
                .update(last_scan=None)
            # Delete scans
            scan_pks = PackageScan.objects.filter(package_id__in=package_pks)\
                .values_list('pk', flat=True)
            if scan_pks:
                scan_pks = ','.join(str(pk) for pk in scan_pks)
                cursor.execute("DELETE FROM shipments_location WHERE id IN (%s)" % scan_pks)
            package_pks = ','.join(str(pk) for pk in package_pks)
            cursor.execute("DELETE FROM shipments_package WHERE id IN (%s)" % package_pks)

        # Remove any report data specific to this shipment
        DonorShipmentData.objects.filter(shipment=self).delete()

        # delete shipment itself
        self.delete()

        # Now, update
        from reports.signals import _update_donor_category_data
        for (donor_id, category_id) in donor_categories:
            _update_donor_category_data(donor_id, category_id)


class ShipmentDBView(ShipmentMixin, models.Model):
    """Dummy model to represent the database view that computes the shipment statistics"""
    description = models.CharField(max_length=255)
    shipment_date = models.DateField()
    store_release = models.CharField(max_length=45)
    date_in_transit = models.DateField(blank=True, null=True)
    date_picked_up = models.DateField(blank=True, null=True)
    date_expected = models.DateField(blank=True, null=True)
    date_received = models.DateField(blank=True, null=True)
    status = models.IntegerField(choices=Shipment.SHIPMENT_STATUS_CHOICES,
                                 default=Shipment.STATUS_IN_PROGRESS)
    transporter = models.ForeignKey(Transporter, blank=True, null=True,
                                    # This is a view, we don't need to do anything
                                    on_delete=models.DO_NOTHING,
                                    )
    partner = models.ForeignKey(CtsUser,
                                limit_choices_to={'role': ROLE_PARTNER},
                                on_delete=models.DO_NOTHING,
                                )
    acceptable = models.BooleanField(default=False, blank=True)
    status_note = models.TextField(blank=True)
    price_usd = USDCurrencyField(
        verbose_name='Price USD',
        help_text='Price of one unit in US dollars',
    )
    price_local = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0.0)],
        verbose_name='Price in local currency',
        help_text='Price of one unit in local currency',
        default=Decimal('0.00'),
    )
    num_packages = models.BigIntegerField()  # from view
    num_items = models.IntegerField()  # from view
    num_received_items = models.IntegerField()  # from view
    donor = models.CharField(max_length=45, null=True, blank=True)
    last_scan_status_label = models.CharField(max_length=128, blank=True, null=True)

    class Meta(object):
        db_table = 'shipments_view'
        managed = False
        verbose_name = 'shipment'

    @property
    def packages(self):
        return Package.objects.filter(shipment_id=self.pk)

    """
    Here's how CTS v2 came up with verbose status:

    $package_statuses = array();
    foreach ($shipment->packages as $package) {
      if (empty($package_statuses[$package->status]))
        $package_statuses[$package->status] = 0;
      $package_statuses[$package->status] += 1;

      if ($package->status > $shipment->status) {
        $shipment->status = $package->status;
      }
    }

    if ($shipment->status == STATUS_RECEIVED) {
      $shipment->status_count = $package_statuses[STATUS_RECEIVED];
    }
    else if ($shipment->status == STATUS_IN_TRANSIT) {
      $shipment->status_count = $package_statuses[STATUS_IN_TRANSIT];
    }

  $num_packages = sizeof($shipment->packages);
  $status_string = lang("package.status.$shipment->status");
  if (!empty($shipment->status_count) && $shipment->status_count < $num_packages) {
    $status_string .= " (" . number_format($shipment->status_count / $num_packages * 100, 0) . '%)';
  }

    Some conclusions:
      We should only see percents added if the shipment status is received or in transit.
      The percentage shown is the percentage of packages with the same status as the shipment.
      We should only see percentages if there's at least one package (otherwise, the code above
        would never set any values in $package_statuses).
      We should only see percentages less than 100.
    """

    def get_verbose_status(self):
        status_code = self.status
        status_text = status_as_string(status_code)
        if status_code in [Shipment.STATUS_RECEIVED, Shipment.STATUS_IN_TRANSIT]:
            status_count = self.get_status_count(status_code)
            if self.num_packages and status_count < self.num_packages:
                status_text += " (%d%%)" % (100 * status_count // self.num_packages)
        return status_text

    def percent_items_received(self):
        return "%d%%" % (100 * self.num_received_items // self.num_items)


class PackageMixin(object):
    def get_status(self):
        """
        Package status isn't as simple as just looking at the status field.
        """
        if self.status in (Shipment.STATUS_CANCELED, Shipment.STATUS_LOST,
                           Shipment.STATUS_IN_PROGRESS):
            return self.status
        elif self.date_received:
            return Shipment.STATUS_RECEIVED
        elif self.date_in_transit:
            if self.date_expected and now().date() > self.date_expected:
                return Shipment.STATUS_OVERDUE
            return Shipment.STATUS_IN_TRANSIT
        elif self.date_picked_up:
            return Shipment.STATUS_PICKED_UP
        else:
            return Shipment.STATUS_READY

    def get_status_display(self):
        return status_as_string(self.get_status())

    @property
    def date_expected(self):
        return self.shipment.date_expected


class Package(PackageMixin, models.Model):
    name = models.CharField(max_length=255, default='')
    description = models.CharField(max_length=255, default='', blank=True)
    shipment = models.ForeignKey(Shipment,
                                 on_delete=models.CASCADE,
                                 related_name='packages',
                                 db_index=True)
    number_in_shipment = models.IntegerField(
        help_text="The number assigned to this package in the shipment. "
                  "Packages in a shipment are numbered, starting with 1. "
    )
    status = models.IntegerField(blank=True, null=True,
                                 choices=Shipment.SHIPMENT_STATUS_CHOICES,
                                 default=Shipment.STATUS_IN_PROGRESS)
    code = models.CharField(max_length=45, unique=True)
    kit = models.ForeignKey('shipments.Kit', blank=True, null=True)
    last_scan = models.ForeignKey('shipments.PackageScan', blank=True, null=True,
                                  on_delete=models.SET_NULL,
                                  related_name="last_packages")
    # No, I don't know the difference between date picked up and date in transit.
    date_picked_up = models.DateTimeField(blank=True, null=True, default=None)
    date_in_transit = models.DateTimeField(blank=True, null=True, default=None)
    date_received = models.DateTimeField(blank=True, null=True, default=None)

    # TODO: Can this be combined with last_scan?
    last_scan_status_label = models.CharField(max_length=128, blank=True, null=True)

    def __unicode__(self):
        return (u'Package #%d %s in shipment %s'
                % (self.number_in_shipment, self.name, self.shipment))

    class Meta(object):
        ordering = ['shipment', 'number_in_shipment', 'name']
        unique_together = [
            ('shipment', 'number_in_shipment'),
        ]
        index_together = [
            ('shipment', 'number_in_shipment'),
        ]

    def save(self, *args, **kwargs):
        # Make sure the package has a number_in_shipment
        if self.number_in_shipment is None:
            self.number_in_shipment = self.shipment.next_package_number_in_shipment()
        # make sure the package has a code (for QR)
        if not self.code:
            # Assign a code deterministically that should be unique across CTS v3 packages.
            # e.g. "/JO27.3", "/JO27.4", ...
            self.code = '%s%d.%d' % (settings.PREFIX_URL, self.shipment_id, self.number_in_shipment)
        # possibly update shipment status
        if (self.status >= Shipment.STATUS_PICKED_UP
                and self.shipment.status < Shipment.STATUS_PICKED_UP):
            self.shipment.status = Shipment.STATUS_PICKED_UP
            self.shipment.save()
        super(Package, self).save(*args, **kwargs)

    @classmethod
    def make_from_kit(cls, shipment, kit, quantity):
        """
        Create and return a Package by adding `quantity` copies of the
        contents of the Kit to a new package.
        Returns the new package.
        """
        with transaction.atomic():
            pkg = cls.objects.create(
                shipment=shipment,
                name=kit.name,
                description=kit.description,
            )
            for kit_item in kit.items.all():
                PackageItem.from_kit_item(pkg, kit_item, kit_item.quantity * quantity)
        return pkg

    def compute_price_usd(self):
        return sum(item.quantity * item.price_usd for item in self.items.all())

    def compute_price_local(self):
        return sum(item.quantity * item.price_local for item in self.items.all())

    @property
    def scans_data(self):
        """Distinct list of scan records for the package"""
        data = self.scans.all().values('when', 'latitude', 'longitude').distinct()
        return list(data)

    @property
    def num_items(self):
        return self.items.aggregate(num_items=Sum('quantity'))['num_items']

    def name_or_description(self):
        """Return name if not blank, else description if not blank, else blank"""
        return self.name.strip() or self.description.strip() or ''


class PackageDBView(PackageMixin, models.Model):
    # Fake model we can use to reference the view
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    shipment = models.ForeignKey(ShipmentDBView, null=True, blank=True,
                                 on_delete=models.DO_NOTHING,
                                 related_name='packages',
                                 db_index=True)
    number_in_shipment = models.IntegerField(
        null=True, blank=True, default=None,
        help_text="The number assigned to this package in the shipment. "
                  "Packages in a shipment are numbered, starting with 1. "
                  "The numbers are assigned when a shipment is finalized. "
    )
    status = models.IntegerField(blank=True, null=True,
                                 choices=Shipment.SHIPMENT_STATUS_CHOICES)
    code = models.CharField(max_length=45, blank=True)
    kit = models.ForeignKey('shipments.Kit', blank=True, null=True,
                            # This is a view, we don't need to do anything
                            on_delete=models.DO_NOTHING,
                            )
    date_received = models.DateTimeField(blank=True, null=True, default=None)
    date_in_transit = models.DateTimeField(blank=True, null=True, default=None)
    date_received = models.DateTimeField(blank=True, null=True, default=None)

    # Fields that only exist in the view:

    # Sum of quantity * price_usd for each item in this package.
    price_usd = USDCurrencyField(
        verbose_name='Price USD',
        help_text='Price of one unit in US dollars',
    )
    # Sum of quantity * price_local for each item in this package.
    price_local = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0.0)],
        verbose_name='Price in local currency',
        help_text='Price of one unit in local currency',
        default=Decimal('0.00'),
    )
    # Sum of quantity for each item in this package.
    num_items = models.IntegerField()

    last_scan = models.ForeignKey('shipments.PackageScan', blank=True, null=True,
                                  on_delete=models.DO_NOTHING)

    last_scan_status_label = models.CharField(max_length=128, blank=True, null=True)

    class Meta(object):
        managed = False
        db_table = 'packages_view'
        verbose_name = 'package'

    def __unicode__(self):
        return u'Package %s in shipment %s' % (self.name, self.shipment)

    def get_verbose_status(self):
        return status_as_string(self.status)


class KitItem(models.Model):
    """
    An item in a kit.
    """
    kit = models.ForeignKey('Kit', related_name='items')
    catalog_item = models.ForeignKey('catalog.CatalogItem')
    quantity = models.IntegerField(
        default=1,
        help_text="Number of this item to include in a package when making the "
                  "package from this kit."
    )

    class Meta(object):
        ordering = ['kit', 'catalog_item']

    def __unicode__(self):
        return u"Item %s in kit %s" % (self.description, self.kit)

    @property
    def description(self):
        return self.catalog_item.description

    @property
    def item_category(self):
        return self.catalog_item.item_category

    @property
    def price_usd(self):
        return self.catalog_item.price_usd

    @property
    def price_local(self):
        return self.catalog_item.price_local


class Kit(models.Model):
    name = models.CharField(max_length=255, unique=True, default='')
    description = models.CharField(max_length=255, default='', blank=True)

    def __unicode__(self):
        return u"Kit %s" % self.name

    @property
    def num_items(self):
        return sum([item.quantity for item in self.items.all()])

    @property
    def price_usd(self):
        return sum([item.quantity * item.catalog_item.price_usd for item in self.items.all()])

    @property
    def price_local(self):
        return sum([item.quantity * item.catalog_item.price_local for item in self.items.all()])

    class Meta(object):
        ordering = ['name']


class PackageItem(models.Model):
    """Some quantity of one catalog item in a package"""
    description = models.CharField(max_length=255, blank=True)
    unit = models.CharField(max_length=255, blank=True)

    # THESE ARE THE PRICE OF ONE UNIT OF THE ITEM.
    # MULTIPLY BY THE QUANTITY TO GET THE PRICE OF ALL OF THIS ITEM IN THE PACKAGE.
    price_usd = USDCurrencyField(
        verbose_name='Price USD',
        help_text='Price of one unit in US dollars',
    )
    price_local = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0.0)],
        verbose_name='Price in local currency',
        help_text='Price of one unit in local currency',
        default=Decimal('0.00'),
    )

    item_category = models.ForeignKey(
        'catalog.ItemCategory', db_column='item_category',
        on_delete=models.PROTECT,
        blank=True, null=True,
        related_name="%(app_label)s_%(class)s_items",  # e.g. shipments_kititem_items
    )
    donor = models.ForeignKey(Donor, blank=True, null=True, on_delete=models.PROTECT)
    donor_t1 = models.ForeignKey(
        DonorCode,
        limit_choices_to={'donor_code_type': DonorCode.T1},
        related_name='t1_package_items',
        blank=True, null=True,
        on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, blank=True, null=True, on_delete=models.PROTECT,
                                 related_name='package_items')
    weight = models.FloatField(default=0.0,
                               validators=[MinValueValidator(0.0)],
                               help_text='Weight of one unit',
                               blank=True,
                               null=True,
                               )

    # These are the new fields. The ones above all come from CatalogItem.
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='items')
    quantity = models.IntegerField(default=1)
    catalog_item = models.ForeignKey('catalog.CatalogItem', blank=True, null=True)

    def __unicode__(self):
        return "Package item `%s' in package `%s'" % (self.get_description(), self.package)

    def save(self, *args, **kwargs):
        super(PackageItem, self).save(*args, **kwargs)
        if self.package and self.package.shipment:
            # Possibly update donor in shipment object
            donor = self.package.shipment.compute_donor_name()
            if donor != self.package.shipment.donor:
                self.package.shipment.save()

    def get_description(self):
        if self.description:
            return self.description
        if self.catalog_item:
            return self.catalog_item.description
        return ''

    def get_unit(self):
        if self.unit:
            return self.unit
        if self.catalog_item:
            return self.catalog_item.unit
        return ''

    @staticmethod
    def from_kit_item(package, kit_item, quantity=None, save=True):
        """
        Create and return a new package item from the given kit item,
        as part of the specified package.

        Pass save=False if you don't want the model object saved yet,
        e.g. if you want to use bulk_create.
        """
        if quantity is None:
            quantity = kit_item.quantity
        return PackageItem.from_catalog_item(
            package=package,
            catalog_item=kit_item.catalog_item,
            quantity=quantity,
            save=save)

    @staticmethod
    def from_catalog_item(package, catalog_item, quantity, save=True):
        item = PackageItem(
            package=package,
            quantity=quantity,
            catalog_item=catalog_item,
            description=catalog_item.description,
            unit=catalog_item.unit,
            price_usd=catalog_item.price_usd,
            price_local=catalog_item.price_local,
            item_category=catalog_item.item_category,
            donor=catalog_item.donor,
            donor_t1=catalog_item.donor_t1,
            supplier=catalog_item.supplier,
            weight=catalog_item.weight,
        )
        if save:
            item.save()
        return item

    @property
    def extended_price_usd(self):
        return self.quantity * self.price_usd

    @property
    def extended_price_local(self):
        return self.quantity * self.price_local


class PackageItemDBView(models.Model):
    """Some quantity of one catalog item in a package"""
    description = models.CharField(max_length=255, blank=True)
    unit = models.CharField(max_length=255, blank=True)

    # THESE ARE THE PRICE OF ONE UNIT OF THE ITEM.
    # MULTIPLY BY THE QUANTITY TO GET THE PRICE OF ALL OF THIS ITEM IN THE PACKAGE.
    price_usd = USDCurrencyField(
        verbose_name='Price USD',
        help_text='Price of one unit in US dollars',
    )
    price_local = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0.0)],
        verbose_name='Price in local currency',
        help_text='Price of one unit in local currency',
        default=Decimal('0.00'),
    )

    item_category = models.ForeignKey(
        'catalog.ItemCategory', db_column='item_category',
        on_delete=models.DO_NOTHING,
        blank=True, null=True,
        related_name="%(app_label)s_%(class)s_items",  # e.g. shipments_kititem_items
    )
    donor = models.ForeignKey(Donor, blank=True, null=True, on_delete=models.DO_NOTHING)
    donor_t1 = models.ForeignKey(
        DonorCode,
        limit_choices_to={'donor_code_type': DonorCode.T1},
        related_name='t1_package_db_vie_items',
        blank=True, null=True,
        on_delete=models.DO_NOTHING)
    supplier = models.ForeignKey(Supplier, blank=True, null=True, on_delete=models.DO_NOTHING,
                                 related_name='package_db_view_items')
    weight = models.FloatField(default=0.0,
                               validators=[MinValueValidator(0.0)],
                               help_text='Weight of one unit',
                               blank=True,
                               null=True,
                               )

    # These are the new fields. The ones above all come from CatalogItem.
    package = models.ForeignKey(Package, on_delete=models.DO_NOTHING, related_name='db_view_items')
    quantity = models.IntegerField(default=1)
    catalog_item = models.ForeignKey('catalog.CatalogItem',
                                     blank=True, null=True, on_delete=models.DO_NOTHING)

    # These are the faux fields computed by the view
    extended_price_usd = USDCurrencyField(
        verbose_name='Price USD',
        help_text='Price of all units in this package item in US dollars',
    )
    extended_price_local = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0.0)],
        verbose_name='Price in local currency',
        help_text='Price of all units in this package item in local currency',
        default=Decimal('0.00'),
    )

    class Meta(object):
        managed = False
        db_table = 'package_items_view'
        verbose_name = "package item"


class PackageScan(models.Model):
    package = models.ForeignKey(Package, related_name='scans', db_index=True)
    # Storing shipment is redundant but speeds up generating maps by shipment
    shipment = models.ForeignKey(Shipment, related_name='scans')
    longitude = models.DecimalField(decimal_places=10, max_digits=13, null=True)
    latitude = models.DecimalField(decimal_places=10, max_digits=13, null=True)
    altitude = models.DecimalField(decimal_places=6, max_digits=13,
                                   null=True, blank=True, default=None)
    accuracy = models.DecimalField(decimal_places=6, max_digits=13,
                                   null=True, blank=True, default=None)
    when = models.DateTimeField(db_index=True)
    country = models.ForeignKey('shipments.WorldBorder', blank=True, null=True)
    status_label = models.CharField(max_length=128, blank=True, null=True)

    class Meta(object):
        db_table = 'shipments_location'  # We renamed the model, but not the table
        ordering = ['-when']

    def __unicode__(self):
        return u"Package %s at latitude: %s, longitude: %s" % (
            self.package, self.latitude, self.longitude
        )

    @property
    def lat_lng(self):
        return [self.latitude, self.longitude]

    def save(self, *args, **kwargs):
        if self.package:
            self.shipment = self.package.shipment
        if not self.country and self.longitude and self.latitude:
            point = 'POINT (%s %s )' % (self.longitude, self.latitude)
            qs = WorldBorder.objects.filter(mpoly__contains=point)
            if qs:
                self.country = qs[0]
        super(PackageScan, self).save(*args, **kwargs)


class WorldBorder(gis_models.Model):
    # Regular Django fields corresponding to the attributes in the
    # world borders shapefile.
    name = models.CharField(max_length=50)
    area = models.IntegerField()
    pop2005 = models.IntegerField('Population 2005')
    fips = models.CharField('FIPS Code', max_length=2)
    iso2 = models.CharField('2 Digit ISO', max_length=2)
    iso3 = models.CharField('3 Digit ISO', max_length=3)
    un = models.IntegerField('United Nations Code')
    region = models.IntegerField('Region Code')
    subregion = models.IntegerField('Sub-Region Code')
    lon = models.FloatField()
    lat = models.FloatField()

    # GeoDjango-specific: a geometry field (MultiPolygonField), and
    # overriding the default manager with a GeoManager instance.
    mpoly = gis_models.MultiPolygonField()
    objects = gis_models.GeoManager()

    # Returns the string representation of the model.
    def __unicode__(self):
        return self.name

    class Meta(object):
        ordering = ['name']


def status_as_string(status_code):
    return dict(Shipment.SHIPMENT_STATUS_CHOICES)[status_code]
