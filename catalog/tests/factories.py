import factory

from catalog.models import DonorCode


class ItemCategoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = 'catalog.ItemCategory'


class CatalogItemFactory(factory.DjangoModelFactory):
    FACTORY_FOR = 'catalog.CatalogItem'

    item_category = factory.SubFactory(ItemCategoryFactory)
    item_code = factory.Sequence(lambda n: "i%04d" % n)


class DonorCodeT1Factory(factory.DjangoModelFactory):
    FACTORY_FOR = 'catalog.DonorCode'

    code = factory.Sequence(lambda n: 'donor-code-%s' % n)
    donor_code_type = DonorCode.T1


class DonorCodeT3Factory(DonorCodeT1Factory):

    donor_code_type = DonorCode.T3


class DonorFactory(factory.DjangoModelFactory):
    FACTORY_FOR = 'catalog.Donor'

    name = factory.Sequence(lambda n: 'donor-%s' % n)

    @factory.post_generation
    def t1_codes(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of codes were passed in, use them
            for code in extracted:
                self.t1_codes.add(code)

    @factory.post_generation
    def t3_codes(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of codes were passed in, use them
            for code in extracted:
                self.t3_codes.add(code)


class SupplierFactory(factory.DjangoModelFactory):
    FACTORY_FOR = 'catalog.Supplier'

    name = factory.Sequence(lambda n: 'supplier-%d' % n)


class TransporterFactory(factory.DjangoModelFactory):
    FACTORY_FOR = 'catalog.Transporter'
