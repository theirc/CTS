from django.core.urlresolvers import reverse
from django.test import TestCase


class HealthViewTest(TestCase):
    def test_health_view(self):
        # Should get 200, without logging in or anything
        rsp = self.client.get(reverse('health'))
        self.assertEqual(200, rsp.status_code)

    def test_health_url(self):
        # Load balancers will be configured to visit "/health/", so our view
        # has to be there
        rsp = self.client.get('/health/')
        self.assertEqual(200, rsp.status_code)
