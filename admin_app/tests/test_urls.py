"""Smoke tests for URL routing."""
from django.test import SimpleTestCase
from django.urls import reverse


class RootUrlTests(SimpleTestCase):
    def test_root_redirects_to_admin(self):
        r = self.client.get('/', follow=False)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.headers.get('Location'), '/admin/')

    def test_admin_resolves(self):
        self.assertEqual(reverse('admin:index'), '/admin/')
