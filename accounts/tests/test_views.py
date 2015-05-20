from django.contrib.auth import authenticate
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from accounts.models import CtsUser, ROLE_PARTNER, ROLE_OFFICER
from accounts.tests.factories import CtsUserFactory
from accounts.utils import bootstrap_permissions


@override_settings(ONA_DEVICEID_VERIFICATION_FORM_ID=111)
class CtsUserViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        bootstrap_permissions()

    def setUp(self):
        self.user = CtsUserFactory(email='joe@example.com', password='6pack')
        assert self.client.login(email='joe@example.com', password="6pack")

    def test_login_required(self):
        self.client.logout()
        rsp = self.client.get(reverse('user_list'))
        expected_url = reverse('account_login') + '?next=' + reverse('user_list')
        self.assertRedirects(rsp, expected_url)

    def test_list(self):
        user = CtsUserFactory()
        rsp = self.client.get(reverse('user_list'))
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, user.name, msg_prefix=rsp.content.decode('utf-8'))

    def test_create(self):
        # Create a user
        # Get the form page
        url = reverse('new_cts_user_modal')
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertIn('form', rsp.context)
        # Submit the new object
        data = {
            'name': 'test',
            'email': 'test@test.com',
            'mobile': '999',
            'skype': 'testtest',
            'role': ROLE_PARTNER,
            'is_active': True,
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors.as_text())
        self.assertEqual(rsp.status_code, 200)
        user = CtsUser.objects.get(email='test@test.com')
        self.assertEqual(user.role, ROLE_PARTNER)
        # email was sent to set password
        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)
        # Verify that the subject of the first message is correct.
        self.assertIn("New account", mail.outbox[0].subject)

    def test_create_duplicate_email(self):
        data = {
            'name': 'test',
            'email': 'test@test.com',
            'mobile': '999',
            'skype': 'testtest',
            'role': ROLE_PARTNER,
            'is_active': True,
        }
        CtsUserFactory(email=data['email'])
        url = reverse('new_cts_user_modal')
        rsp = self.client.post(url, data=data)
        self.assertEqual(400, rsp.status_code)

    def test_create_with_password(self):
        # Create a user and specify a password
        # Get the form page
        url = reverse('new_cts_user_modal')
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertIn('form', rsp.context)
        # Submit the new object
        new_password = 'prettykitty'
        data = {
            'name': 'test',
            'email': 'test@test.com',
            'mobile': '999',
            'skype': 'testtest',
            'role': ROLE_PARTNER,
            'is_active': True,
            'password1': new_password,
            'password2': new_password,
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors.as_text())
        self.assertEqual(rsp.status_code, 200)
        user = CtsUser.objects.get(email='test@test.com')
        self.assertEqual(user.role, ROLE_PARTNER)
        # email was NOT sent to set password
        # Test that no message has been sent.
        self.assertEqual(len(mail.outbox), 0)
        # Validate password
        self.assertEqual(user, authenticate(email='test@test.com', password=new_password))

    def test_update(self):
        # Update a user
        user = self.user
        url = reverse('edit_cts_user_modal', args=[user.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Submit the new object
        email = "edited@example.com"
        data = {
            'name': 'test',
            'email': email,
            'mobile': '999',
            'skype': 'testtest',
            'role': ROLE_PARTNER,
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(rsp.status_code, 200)
        user2 = CtsUser.objects.get(email=email)
        self.assertEqual(user.pk, user2.pk)
        self.assertEqual(user2.role, ROLE_PARTNER)

    def test_password_change(self):
        # Change a user's password
        old_password = '6pack'
        user = self.user
        old_email = user.email
        self.assertEqual(user, authenticate(email=old_email, password=old_password))
        url = reverse('edit_cts_user_modal', args=[user.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        # Submit the new object
        new_email = "edited@example.com"
        new_password = 'foobar'
        data = {
            'name': 'test',
            'email': new_email,
            'mobile': '999',
            'skype': 'testtest',
            'role': ROLE_PARTNER,
            'password1': new_password,
            'password2': new_password,
        }
        rsp = self.client.post(url, data=data)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertEqual(rsp.status_code, 200)
        user = CtsUser.objects.get(pk=user.pk)
        self.assertEqual(user, authenticate(email=new_email, password=new_password))

    def test_delete(self):
        # Delete a user
        # Need to be logged in as one user, then delete another user
        user = CtsUserFactory()
        url = reverse('user_delete', args=[user.pk])
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertContains(rsp, 'Confirm')
        CtsUser.objects.get(pk=user.pk)
        # Now delete it!
        # Should really just change them to not active.
        rsp = self.client.post(url)
        if rsp.status_code == 400:
            self.fail(rsp.context['form'].errors)
        self.assertRedirects(rsp, reverse('user_list'))
        user = CtsUser.objects.get(pk=user.pk)
        self.assertFalse(user.is_active)

    def test_edit_modal(self):
        user = self.user
        url = reverse('edit_cts_user_modal', kwargs={'pk': user.pk})
        rsp = self.client.get(url)
        self.assertEqual(200, rsp.status_code)
        self.assertTemplateUsed(rsp, 'accounts/ctsuser_edit_modal.html')

    def test_reset_api_token_get(self):
        user = self.user
        url = reverse('reset_api_token', kwargs={'pk': user.pk})
        rsp = self.client.get(url)
        self.assertEqual(405, rsp.status_code)

    def test_reset_api_token_post(self):
        user = self.user
        original_token = user.auth_token.key
        url = reverse('reset_api_token', kwargs={'pk': user.pk})
        rsp = self.client.post(url)
        self.assertRedirects(rsp, reverse('user_list'))
        user = CtsUser.objects.get(pk=user.pk)
        self.assertNotEqual(original_token, user.auth_token.key)

    def test_reset_api_token_post_without_permission(self):
        self.user.role = ROLE_PARTNER  # least permissions
        self.user.save()
        user = CtsUserFactory()
        original_token = user.auth_token.key
        url = reverse('reset_api_token', kwargs={'pk': user.pk})
        rsp = self.client.post(url)
        self.assertEqual(403, rsp.status_code)
        user = CtsUser.objects.get(pk=user.pk)
        self.assertEqual(original_token, user.auth_token.key)

    def test_home_view_not_logged_in(self):
        self.client.logout()
        rsp = self.client.get(reverse('home'))
        self.assertRedirects(rsp, reverse('account_login'))

    def test_home_view_with_catalog_perms(self):
        self.user.role = ROLE_OFFICER
        self.user.save()
        rsp = self.client.get(reverse('home'))
        self.assertRedirects(rsp, reverse('catalog_list'))

    def test_home_view_without_catalog_perms(self):
        self.user.role = ROLE_PARTNER
        self.user.save()
        rsp = self.client.get(reverse('home'))
        self.assertRedirects(rsp, reverse('reports_list'))
