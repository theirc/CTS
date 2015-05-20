import factory

from accounts.models import ROLE_COORDINATOR, CtsUser, ROLE_PARTNER


class CtsUserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = 'accounts.CtsUser'

    email = factory.Sequence(lambda n: "user%d@example.com" % n)
    mobile = factory.Sequence(lambda n: "+%d" % n)
    password = CtsUser.objects.make_random_password()
    # Default to most privileged role
    role = ROLE_COORDINATOR

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        manager = cls._get_manager(model_class)
        is_superuser = kwargs.pop('is_superuser', False)
        if is_superuser:
            return manager.create_superuser(*args, **kwargs)
        else:
            # The default would use ``manager.create(*args, **kwargs)``
            return manager.create_user(*args, **kwargs)


class PartnerFactory(CtsUserFactory):
    role = ROLE_PARTNER
