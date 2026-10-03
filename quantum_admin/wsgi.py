"""
WSGI config for quantum_admin project.
TODO: Production — systemd/Gunicorn must set DJANGO_SETTINGS_MODULE=quantum_admin.settings.prod
(see deploy.prod.sh). This module default is dev for local runs only.
"""
import os

# Prefer mysqlclient (Django 5.1+); fall back to PyMySQL shim when mysqlclient is not built (e.g. some local setups).
try:
    import MySQLdb  # noqa: F401
except ImportError:
    import pymysql
    pymysql.install_as_MySQLdb()

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quantum_admin.settings.dev')

application = get_wsgi_application()
