"""
Django staging settings for quantum-edu-admin.
"""
import os

from .base import *

DEBUG = True

_allowed = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]

# RDS MySQL - admin_django and quantum_education on same host
_mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
_mysql_port = os.environ.get('MYSQL_PORT', '3306')
_mysql_user = os.environ.get('MYSQL_USER', 'admin')
_mysql_password = os.environ.get('MYSQL_PASSWORD', '')
_mysql_db = os.environ.get('MYSQL_DATABASE', 'defaultdb')

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

# Log 500 errors and R2 upload flow to stderr (visible in journalctl)
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
