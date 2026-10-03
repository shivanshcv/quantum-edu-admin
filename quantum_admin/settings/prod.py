"""
Django production settings for quantum-edu-admin.
"""
import os

from .base import *

DEBUG = False

_allowed = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]
_render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)

# Served over HTTPS behind a reverse proxy (Caddy/nginx) that terminates TLS.
_csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()] or [
    f'https://{h}' for h in ALLOWED_HOSTS if h not in ('localhost', '127.0.0.1')
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Production MySQL - must be set via env vars
_mysql_host = os.environ.get('MYSQL_HOST', '')
_mysql_port = os.environ.get('MYSQL_PORT', '3306')
_mysql_user = os.environ.get('MYSQL_USER', '')
_mysql_password = os.environ.get('MYSQL_PASSWORD', '')
_mysql_db = os.environ.get('MYSQL_DATABASE', 'quantum_education')

_mysql_options = {
    'charset': 'utf8mb4',
    'init_command': "SET time_zone = '+05:30';",
}

_mysql_options_tls = {**_mysql_options, **mysql_rds_tls_fragment()}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_ADMIN_DB', 'admin_django'),
        'USER': _mysql_user,
        'PASSWORD': _mysql_password,
        'HOST': _mysql_host,
        'PORT': _mysql_port,
        'OPTIONS': _mysql_options_tls,
    },
    'quantum_education': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': _mysql_db,
        'USER': _mysql_user,
        'PASSWORD': _mysql_password,
        'HOST': _mysql_host,
        'PORT': _mysql_port,
        'OPTIONS': _mysql_options_tls,
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'admin_app': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
