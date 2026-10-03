"""
Django base settings for quantum-edu-admin.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'admin_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'quantum_admin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'admin_app' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'quantum_admin.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Allow larger file uploads (videos up to 100MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB in memory; larger use temp file
DATA_UPLOAD_MAX_MEMORY_SIZE = 150 * 1024 * 1024  # 150MB max request (for video upload)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Database router: admin_app models use quantum_education, others use default (admin_django)
DATABASE_ROUTERS = ['admin_app.db_router.QuantumEducationRouter']

# Cloudflare R2 (S3-compatible) for media uploads
R2_ACCOUNT_ID = os.environ.get('R2_ACCOUNT_ID', '')
R2_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID', '')
R2_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY', '')
R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME', 'quantum-edu-media')
R2_PUBLIC_URL = os.environ.get('R2_PUBLIC_URL', 'https://pub-96a817cca5de440db5e3364bbb57f3ed.r2.dev')
R2_ENABLED = bool(R2_ACCOUNT_ID and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY)


def mysql_rds_tls_options_for_version(version_info):
    """
    RDS TLS fragment for Django MySQL OPTIONS.

    Django 5.1+ requires mysqlclient (MySQLdb) 2.2.1+; that driver accepts ssl_mode.
    PyMySQL's MySQLdb shim reports 1.x and does not support ssl_mode — use an ssl dict.
    """
    prefix = (0, 0, 0)
    if isinstance(version_info, (tuple, list)) and len(version_info) >= 3:
        prefix = tuple(int(x) for x in version_info[:3])
    if prefix >= (2, 2, 1):
        return {'ssl_mode': 'REQUIRED'}
    return {'ssl': {'check_hostname': False}}


def mysql_rds_tls_fragment():
    try:
        import MySQLdb
        return mysql_rds_tls_options_for_version(getattr(MySQLdb, 'version_info', (0, 0, 0)))
    except ImportError:
        return mysql_rds_tls_options_for_version((0, 0, 0))
