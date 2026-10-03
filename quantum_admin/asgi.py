"""
ASGI config for quantum_admin project.
"""
import os

# Use PyMySQL as MySQLdb if mysqlclient not installed (e.g. macOS). EC2 typically has mysqlclient.
try:
    import MySQLdb  # noqa: F401
except ImportError:
    import pymysql
    pymysql.install_as_MySQLdb()

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quantum_admin.settings.dev')

application = get_asgi_application()
