from django.contrib.auth.models import Group
import mock

from django.test import TestCase
from accounts.utils import bootstrap_permissions, get_permission_by_name, canonical_email


class BootstrapPermissionsTest(TestCase):
    def assertGroupHasPermission(self, group, perm_name):
        permission = get_permission_by_name(perm_name)
        self.assertTrue(group.permissions.filter(pk=permission.pk).exists())

    def assertGroupNoPermission(self, group, perm_name):
        permission = get_permission_by_name(perm_name)
        self.assertFalse(group.permissions.filter(pk=permission.pk).exists())

    @mock.patch('accounts.utils.ROLE_PERMISSIONS', {'role': ['shipments.do_something']})
    def test_simple_case(self):
        bootstrap_permissions()
        group = Group.objects.get(name='role')
        self.assertGroupHasPermission(group, 'shipments.do_something')
        perm = get_permission_by_name('shipments.do_something')
        self.assertEqual('Can do something', perm.name)

    @mock.patch('accounts.utils.ROLE_PERMISSIONS', {'role1': ['shipments.do_something',
                                                              'shipments.something_else'],
                                                    'role2': ['shipments.do_something',
                                                              'shipments.a_third_thing']})
    def test_two_groups(self):
        bootstrap_permissions()
        group1 = Group.objects.get(name='role1')
        self.assertGroupHasPermission(group1, 'shipments.do_something')
        self.assertGroupHasPermission(group1, 'shipments.something_else')
        self.assertGroupNoPermission(group1, 'shipments.a_third_thing')
        group2 = Group.objects.get(name='role2')
        self.assertGroupHasPermission(group2, 'shipments.do_something')
        self.assertGroupNoPermission(group2, 'shipments.something_else')
        self.assertGroupHasPermission(group2, 'shipments.a_third_thing')

    def test_removing_permissions(self):
        # If we remove permissions from the ROLE_PERMISSIONS structure and run
        # bootstrap_permissions again, the removed permissions get removed from the group.
        # BIG CAVEAT though - we only do this for permissions that are granted elsewhere
        # in ROLE_PERMISSIONS, because we don't want to accidentally remove other permissions
        # that someone might have added manually.
        with mock.patch('accounts.utils.ROLE_PERMISSIONS', {'role1': ['shipments.do_something',
                                                                      'shipments.something_else'],
                                                            'role2': ['shipments.something_else']}):
            bootstrap_permissions()
        group1 = Group.objects.get(name='role1')
        self.assertGroupHasPermission(group1, 'shipments.do_something')
        self.assertGroupHasPermission(group1, 'shipments.something_else')
        with mock.patch('accounts.utils.ROLE_PERMISSIONS', {'role1': ['shipments.do_something'],
                                                            'role2': ['shipments.something_else']}):
            bootstrap_permissions()
        self.assertGroupHasPermission(group1, 'shipments.do_something')
        self.assertGroupNoPermission(group1, 'shipments.something_else')

    @mock.patch('accounts.utils.ROLE_PERMISSIONS', {'role1': ['shipments.do_something',
                                                              'shipments.something_else'],
                                                    'role2': ['shipments.a_third_thing']})
    @mock.patch('accounts.utils.IMPLIED_ROLES', {'role2': ['role1']})
    def test_implied_permissions(self):
        bootstrap_permissions()
        group1 = Group.objects.get(name='role1')
        self.assertGroupHasPermission(group1, 'shipments.do_something')
        self.assertGroupHasPermission(group1, 'shipments.something_else')
        self.assertGroupNoPermission(group1, 'shipments.a_third_thing')
        group2 = Group.objects.get(name='role2')
        self.assertGroupHasPermission(group2, 'shipments.do_something')
        self.assertGroupHasPermission(group2, 'shipments.something_else')
        self.assertGroupHasPermission(group2, 'shipments.a_third_thing')

    @mock.patch('accounts.utils.ROLE_PERMISSIONS', {'role1': ['shipments.do_something',
                                                              'shipments.something_else'],
                                                    'role2': ['shipments.a_third_thing'],
                                                    'role3': []})
    @mock.patch('accounts.utils.IMPLIED_ROLES', {'role2': ['role1'],
                                                 'role3': ['role2']})
    def test_transitive_implied_permissions(self):
        bootstrap_permissions()
        group3 = Group.objects.get(name='role3')
        self.assertGroupHasPermission(group3, 'shipments.do_something')
        self.assertGroupHasPermission(group3, 'shipments.something_else')
        self.assertGroupHasPermission(group3, 'shipments.a_third_thing')

    @mock.patch('accounts.utils.ROLE_PERMISSIONS', {'role': ['shipments.do_something']})
    def test_extras_not_removed(self):
        # If a group already has some other permissions, running bootstrap
        # will leave them alone
        group = Group.objects.create(name='role')
        group.permissions.add(get_permission_by_name('shipments.existing_permission'))
        bootstrap_permissions()
        self.assertGroupHasPermission(group, 'shipments.do_something')
        self.assertGroupHasPermission(group, 'shipments.existing_permission')


class CanonicalEmailTest(TestCase):
    def test_it(self):
        data = [
            ('foo@example.com', 'foo@example.com'),
            ('foo@EXAMPLE.COM', 'foo@example.com'),
            ('foo+bar@examPle.com', 'foo+bar@example.com')
        ]
        for input, output in data:
            self.assertEqual(output, canonical_email(input))
