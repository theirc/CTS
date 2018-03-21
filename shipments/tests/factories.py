import random

from django.utils import timezone
from factory import DjangoModelFactory, SubFactory, LazyAttribute, Sequence
from accounts.tests.factories import CtsUserFactory

from catalog.tests.factories import CatalogItemFactory, ItemCategoryFactory, DonorFactory, \
    DonorCodeT1Factory, SupplierFactory
from shipments.models import Shipment, Package, PackageItem, Kit, KitItem, PackageScan


class ShipmentFactory(DjangoModelFactory):
    class Meta:
        model = Shipment

    partner = SubFactory(CtsUserFactory)


class PackageFactory(DjangoModelFactory):
    class Meta:
        model = Package

    name = Sequence(lambda n: "Package %d" % n)
    description = Sequence(lambda n: "Package %d description" % n)
    shipment = SubFactory(ShipmentFactory)


class PackageItemFactory(DjangoModelFactory):
    class Meta:
        model = PackageItem

    catalog_item = SubFactory(CatalogItemFactory)
    package = SubFactory(PackageFactory)
    item_category = SubFactory(ItemCategoryFactory)
    donor = SubFactory(DonorFactory)
    donor_t1 = SubFactory(DonorCodeT1Factory)
    supplier = SubFactory(SupplierFactory)


class KitFactory(DjangoModelFactory):
    class Meta:
        model = Kit

    name = Sequence(lambda n: "Kit %d" % n)


class KitItemFactory(DjangoModelFactory):
    class Meta:
        model = KitItem

    kit = SubFactory(KitFactory)
    catalog_item = SubFactory(CatalogItemFactory)
    quantity = LazyAttribute(lambda o: random.choice(range(1, 10)))


class PackageScanFactory(DjangoModelFactory):
    class Meta:
        model = PackageScan

    package = SubFactory(PackageFactory)
    longitude = 36.13
    latitude = 37.10
    when = LazyAttribute(lambda o: timezone.now())
