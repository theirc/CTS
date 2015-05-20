from django.forms import model_to_dict
from django.test import TestCase
from accounts.forms import CtsUserEditForm, CtsUserCreationForm, CtsUserChangeForm
from accounts.models import CtsUser
from accounts.tests.factories import CtsUserFactory


class TestUserEditForm(TestCase):
    def test_user_edit(self):
        user = CtsUserFactory()

        data = model_to_dict(user)
        data['mobile'] = '+1134234'
        form = CtsUserEditForm(instance=user, data=data)
        self.assertTrue(form.is_valid())
        user = form.save()
        user = CtsUser.objects.get(pk=user.pk)
        self.assertEqual(data['mobile'], user.mobile)

    def test_user_edit_duplicate_email(self):
        user = CtsUserFactory()
        user2 = CtsUserFactory()
        data = model_to_dict(user)
        data['email'] = user2.email
        form = CtsUserEditForm(instance=user, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class TestUserCreationForm(TestCase):
    def test_user_create(self):
        data = {
            'email': 'foo@example.com',
            'password1': 'password',
            'password2': 'password',
        }
        form = CtsUserCreationForm(data=data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, data['email'])

    def test_duplicate_email(self):
        data = {
            'email': 'foo@example.com',
            'password1': 'password',
            'password2': 'password',
        }
        initial = {'is_active': True, 'name': '', 'email': ''}
        CtsUserFactory(email=data['email'])
        form = CtsUserCreationForm(initial=initial, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class TestUserChangeForm(TestCase):
    def test_user_edit(self):
        user = CtsUserFactory()

        data = model_to_dict(user)
        data['mobile'] = '+1134234'
        form = CtsUserChangeForm(instance=user, data=data)
        self.assertTrue(form.is_valid())
        user = form.save()
        user = CtsUser.objects.get(pk=user.pk)
        self.assertEqual(data['mobile'], user.mobile)
