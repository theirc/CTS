from factory import DjangoModelFactory, SubFactory
from catalog.tests.factories import DonorFactory, ItemCategoryFactory
from reports.models import DonorShipmentData, DonorCategoryData
from shipments.tests.factories import ShipmentFactory


class DonorShipmentDataFactory(DjangoModelFactory):
    FACTORY_FOR = DonorShipmentData

    donor = SubFactory(DonorFactory)
    shipment = SubFactory(ShipmentFactory)


class DonorCategoryDataFactory(DjangoModelFactory):
    FACTORY_FOR = DonorCategoryData

    donor = SubFactory(DonorFactory)
    category = SubFactory(ItemCategoryFactory)
