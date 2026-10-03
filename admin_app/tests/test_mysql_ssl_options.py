"""RDS MySQL OPTIONS: mysqlclient vs PyMySQL TLS fragments and merged DATABASE settings."""
from django.test import SimpleTestCase

from quantum_admin.settings.base import mysql_rds_tls_options_for_version


class MysqlRdsTlsOptionsTests(SimpleTestCase):
    def test_mysqlclient_22_uses_ssl_mode(self):
        o = mysql_rds_tls_options_for_version((2, 2, 4, 'final', 0))
        self.assertEqual(o, {'ssl_mode': 'REQUIRED'})
        self.assertNotIn('ssl', o)

    def test_pymysql_shim_uses_ssl_dict(self):
        o = mysql_rds_tls_options_for_version((1, 4, 6))
        self.assertIn('ssl', o)
        self.assertIsInstance(o['ssl'], dict)
        self.assertNotIn('ssl_mode', o)

    def test_prod_options_include_tls_fragment(self):
        import quantum_admin.settings.prod as prod

        for alias in ('default', 'quantum_education'):
            with self.subTest(alias=alias):
                opts = prod.DATABASES[alias]['OPTIONS']
                self.assertTrue('ssl_mode' in opts or 'ssl' in opts)

    def test_staging_options_include_tls_fragment(self):
        import quantum_admin.settings.staging as staging

        for alias in ('default', 'quantum_education'):
            with self.subTest(alias=alias):
                opts = staging.DATABASES[alias]['OPTIONS']
                self.assertTrue('ssl_mode' in opts or 'ssl' in opts)
