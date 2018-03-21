import json

from django.test import TestCase

from accounts.models import ROLE_PARTNER
from accounts.tests.factories import CtsUserFactory
from accounts.utils import bootstrap_permissions


class BaseAPITest(TestCase):
    def call_api(self, url, token=None):
        """
        Call API with auth and return the response object
        Assumes self.email and self.password exist.
        """

        """
        For clients to authenticate, the token token should be included in the Authorization
        HTTP header. The token should be prefixed by the string literal "Token", with
        whitespace separating the two strings. For example:

        Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
        """

        token = token or self.user.auth_token.key
        auth_header = "Token %s" % token
        return self.client.get(url,
                               HTTP_ACCEPT='application/json',
                               HTTP_AUTHORIZATION=auth_header,
                               )

    def post_api(self, url, data, token=None):
        """
        Data should be a python object. It'll be jsonified and posted.
        """
        token = token or self.user.auth_token.key
        auth_header = "Token %s" % token
        json_data = json.dumps(data)
        return self.client.post(url,
                                data=json_data,
                                content_type='application/json',
                                HTTP_ACCEPT='application/json',
                                HTTP_AUTHORIZATION=auth_header,
                                )


class APITest(BaseAPITest):
    @classmethod
    def setUpClass(cls):
        super(APITest, cls).setUpClass()
        bootstrap_permissions()

    def setUp(self):
        super(APITest, self).setUp()
        self.email = 'franz@example.com'
        self.password = 'liszt'
        self.user = CtsUserFactory(email=self.email,
                                   password=self.password)

    def test_api_root(self):
        # we should get back a nice JSON listing of what's available
        rsp = self.call_api('/api/')
        self.assertEqual(200, rsp.status_code)
        data_json = rsp.content
        data = json.loads(data_json)
        self.assertIn(u'auth/users', data)
        self.assertIn(u'catalog/items', data)

    def test_api_users(self):
        # The users API should list our test user
        rsp = self.call_api('/api/auth/users/')
        self.assertEqual(200, rsp.status_code)
        print(json.loads(rsp.content))
        data = json.loads(rsp.content)['results']
        user = data[0]
        self.assertEqual(user['email'], self.email)
        self.assertEqual(user['is_active'], True)
        self.assertEqual(user['is_superuser'], False)

    def test_auth(self):
        rsp = self.call_api('/api/auth/users/', token='invalidkey')
        self.assertEqual(401, rsp.status_code)

    def test_model_permissions(self):
        self.user.role = ROLE_PARTNER  # No permissions on users
        self.user.save()
        rsp = self.call_api('/api/auth/users/')
        self.assertEqual(403, rsp.status_code)

    def test_post_user(self):
        # The API is read-only. Any POST should return a 405
        user = CtsUserFactory(name="barney fife")
        rsp = self.call_api('/api/auth/users/%d/' % user.pk)
        self.assertEqual(200, rsp.status_code)
        data = json.loads(rsp.content)
        data['name'] = "Freddy Fife"
        rsp = self.post_api('/api/auth/users/%d/' % user.pk, data=data)
        self.assertEqual(405, rsp.status_code)
