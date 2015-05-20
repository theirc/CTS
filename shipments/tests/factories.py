import random

from django.utils import timezone
from factory import DjangoModelFactory, SubFactory, LazyAttribute, Sequence
from accounts.tests.factories import CtsUserFactory

from catalog.tests.factories import CatalogItemFactory, ItemCategoryFactory, DonorFactory, \
    DonorCodeT1Factory, SupplierFactory
from shipments.models import Shipment, Package, PackageItem, Kit, KitItem, PackageScan


class ShipmentFactory(DjangoModelFactory):
    FACTORY_FOR = Shipment

    partner = SubFactory(CtsUserFactory)


class PackageFactory(DjangoModelFactory):
    FACTORY_FOR = Package

    name = Sequence(lambda n: "Package %d" % n)
    description = Sequence(lambda n: "Package %d description" % n)
    shipment = SubFactory(ShipmentFactory)


class PackageItemFactory(DjangoModelFactory):
    FACTORY_FOR = PackageItem

    catalog_item = SubFactory(CatalogItemFactory)
    package = SubFactory(PackageFactory)
    item_category = SubFactory(ItemCategoryFactory)
    donor = SubFactory(DonorFactory)
    donor_t1 = SubFactory(DonorCodeT1Factory)
    supplier = SubFactory(SupplierFactory)


class KitFactory(DjangoModelFactory):
    FACTORY_FOR = Kit

    name = Sequence(lambda n: "Kit %d" % n)


class KitItemFactory(DjangoModelFactory):
    FACTORY_FOR = KitItem

    kit = SubFactory(KitFactory)
    catalog_item = SubFactory(CatalogItemFactory)
    quantity = LazyAttribute(lambda o: random.choice(range(1, 10)))


class PackageScanFactory(DjangoModelFactory):
    FACTORY_FOR = PackageScan

    package = SubFactory(PackageFactory)
    longitude = 36.13
    latitude = 37.10
    when = LazyAttribute(lambda o: timezone.now())
