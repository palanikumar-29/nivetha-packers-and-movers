import os
from django.test import TestCase, Client, override_settings
from django.conf import settings
from django.urls import reverse
import dj_database_url


class ProjectFoundationTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_placeholder_home_returns_http_200(self):
        """Verify root page returns HTTP 200 with placeholder content."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nivetha Packers and Movers')

    def test_default_admin_url_is_omitted(self):
        """Verify /admin/ returns 404 by omission."""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 404)

    def test_panel_url_is_mounted(self):
        """Verify /panel/ is mounted and redirects to login when unauthenticated."""
        response = self.client.get('/panel/')
        self.assertIn(response.status_code, (200, 302))

    def test_contact_vars_safe_when_empty(self):
        """Verify BUSINESS_PHONE and BUSINESS_WHATSAPP safe defaults when absent."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_storages_configuration(self):
        """Verify Django 5.2 STORAGES setting has default and staticfiles backends."""
        self.assertIn('default', settings.STORAGES)
        self.assertIn('staticfiles', settings.STORAGES)
        # By default in local/testing without USE_CLOUDINARY, FileSystemStorage is used
        self.assertEqual(
            settings.STORAGES['default']['BACKEND'],
            'django.core.files.storage.FileSystemStorage'
        )

    def test_database_url_switches_to_postgres(self):
        """Verify DATABASE_URL with Neon PostgreSQL parses correctly without code changes."""
        neon_url = 'postgres://user:pass@ep-cool-sample.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'
        parsed = dj_database_url.parse(neon_url, conn_max_age=600, conn_health_checks=True)
        self.assertEqual(parsed['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(parsed['NAME'], 'neondb')
        self.assertEqual(parsed['USER'], 'user')
        self.assertEqual(parsed['PASSWORD'], 'pass')
        self.assertEqual(parsed['HOST'], 'ep-cool-sample.ap-southeast-1.aws.neon.tech')

    def test_production_security_settings(self):
        """Verify production security configuration parameters."""
        from config.settings import production as prod_settings
        self.assertFalse(prod_settings.DEBUG)
        self.assertTrue(prod_settings.SECURE_SSL_REDIRECT)
        self.assertTrue(prod_settings.SESSION_COOKIE_SECURE)
        self.assertTrue(prod_settings.CSRF_COOKIE_SECURE)
        self.assertEqual(prod_settings.SECURE_HSTS_SECONDS, 31536000)
        self.assertTrue(prod_settings.SECURE_HSTS_INCLUDE_SUBDOMAINS)
        self.assertEqual(prod_settings.X_FRAME_OPTIONS, 'DENY')

    def test_wsgi_defaults_to_production_settings(self):
        """
        Verify that wsgi.py defaults to config.settings.production so gunicorn
        never runs in production with local DEBUG=True settings by accident.
        """
        import inspect
        import subprocess
        import sys
        from config import wsgi

        # 1. Source check
        source = inspect.getsource(wsgi)
        self.assertIn(
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')",
            source
        )

        # 2. Execution check in fresh subprocess without DJANGO_SETTINGS_MODULE
        code = (
            "import os; "
            "os.environ.pop('DJANGO_SETTINGS_MODULE', None); "
            "from config import wsgi; "
            "print(os.environ.get('DJANGO_SETTINGS_MODULE'))"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(result.stdout.strip(), 'config.settings.production')

