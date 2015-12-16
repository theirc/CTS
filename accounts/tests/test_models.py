import random
import string

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import ROLE_PARTNER, ROLE_COORDINATOR, ROLE_OFFICER, ROLE_MANAGER
from accounts.models import CtsUser
from accounts.tests.factories import CtsUserFactory
from accounts.utils import bootstrap_permissions


class CtsUserModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(CtsUserModelTest, cls).setUpClass()
        bootstrap_permissions()

    def test_hex_color(self):
        # missing #
        user = CtsUserFactory(colour='555aaa')
        with self.assertRaises(ValidationError):
            user.full_clean()
        # not 3 or 6
        user = CtsUserFactory(colour='#5544')
        with self.assertRaises(ValidationError):
            user.full_clean()
        # alpha out of range
        user = CtsUserFactory(colour='#JJJKKK')
        with self.assertRaises(ValidationError):
            user.full_clean()
        # short version
        user.colour = '#FFF'
        user.full_clean()
        # long version
        user.colour = '#FFFCCC'
        user.full_clean()

    def test_mobile_validator(self):
        # text
        user = CtsUserFactory(mobile='555aaa')
        with self.assertRaises(ValidationError):
            user.full_clean()
        # optional +
        user.mobile = '+555'
        user.full_clean()
        # optional -
        user.mobile = '555-555-555'
        user.full_clean()

    def test_skype_validator(self):
        # space
        user = CtsUserFactory(skype='aaa aaa')
        with self.assertRaises(ValidationError):
            user.full_clean()
        # starts with non-letter
        user.skype = '$asdfasdf'
        with self.assertRaises(ValidationError):
            user.full_clean()
        # < 5 chars
        user.skype = 'asdff'
        with self.assertRaises(ValidationError):
            user.full_clean()
        # > 32 chars
        user.skype = ''.join(random.choice(string.lowercase) for i in range(33))
        with self.assertRaises(ValidationError):
            user.full_clean()
        user.skype = ''.join(random.choice(string.lowercase) for i in range(10))
        user.full_clean()

    def test_save_sets_groups(self):
        user = CtsUserFactory(role=ROLE_PARTNER)
        self.assertTrue(user.groups.filter(name=ROLE_PARTNER).exists())
        self.assertFalse(user.groups.filter(name=ROLE_OFFICER).exists())
        self.assertFalse(user.groups.filter(name=ROLE_COORDINATOR).exists())
        user.role = ROLE_OFFICER
        user.save()
        self.assertFalse(user.groups.filter(name=ROLE_PARTNER).exists())
        self.assertTrue(user.groups.filter(name=ROLE_OFFICER).exists())
        self.assertFalse(user.groups.filter(name=ROLE_COORDINATOR).exists())
        user.role = ROLE_COORDINATOR
        user.save()
        self.assertFalse(user.groups.filter(name=ROLE_PARTNER).exists())
        self.assertTrue(user.groups.filter(name=ROLE_OFFICER).exists())
        self.assertTrue(user.groups.filter(name=ROLE_COORDINATOR).exists())
        user.role = ROLE_PARTNER
        user.save()
        self.assertTrue(user.groups.filter(name=ROLE_PARTNER).exists())
        self.assertFalse(user.groups.filter(name=ROLE_OFFICER).exists())
        self.assertFalse(user.groups.filter(name=ROLE_COORDINATOR).exists())

    def test_has_role(self):
        user = CtsUserFactory(role=ROLE_PARTNER)
        self.assertTrue(user.has_role(ROLE_PARTNER))
        self.assertFalse(user.has_role(ROLE_COORDINATOR))
        user.groups.add(Group.objects.get(name=ROLE_COORDINATOR))
        self.assertTrue(user.has_role(ROLE_COORDINATOR))

    def test_add_role(self):
        user = CtsUserFactory(role=ROLE_PARTNER)
        self.assertTrue(user.has_role(ROLE_PARTNER))
        self.assertFalse(user.has_role(ROLE_COORDINATOR))
        user.add_role(ROLE_COORDINATOR)
        self.assertTrue(user.has_role(ROLE_COORDINATOR))

    def test_reset_api_token(self):
        user = CtsUserFactory()
        original_token = user.auth_token.key
        user.reset_api_token()
        user = CtsUser.objects.get(pk=user.pk)
        self.assertNotEqual(original_token, user.auth_token.key)

    def test_is_just_partner(self):
        user = CtsUserFactory(role=ROLE_PARTNER, is_superuser=False)
        self.assertTrue(user.is_just_partner())
        user.role = ROLE_COORDINATOR
        user.save()
        self.assertFalse(user.is_just_partner())
        user.role = ROLE_PARTNER
        user.is_superuser = True
        user.save()
        self.assertFalse(user.is_just_partner())
        user = CtsUserFactory(role=ROLE_PARTNER, is_superuser=False)
        self.assertTrue(user.is_just_partner())
        manager_group = Group.objects.get(name=ROLE_MANAGER)
        user.groups.add(manager_group)
        self.assertFalse(user.is_just_partner())
