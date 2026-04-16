"""
ESCEP Niger — Configuration Django
Plateforme de gestion des mémoires et rapports de stage
"""
from pathlib import Path
from decouple import config
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='unsafe-dev-key')
DEBUG       = config('DEBUG', default=True, cast=bool)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    # Apps ESCEP
    'apps.authentication',
    'apps.etudiant',
    'apps.chef_departement',
    'apps.directeur_etudes',
    'apps.direction_generale',
    'apps.jury',
    'apps.bibliotheque',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.authentication.context_processors.user_role_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'



DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1').split(',')
DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}

AUTH_USER_MODEL = 'authentication.User'
LOGIN_URL           = '/auth/connexion/'
LOGIN_REDIRECT_URL  = '/'
LOGOUT_REDIRECT_URL = '/auth/connexion/'

OTP_VALIDITY_MINUTES = 10
AI_DETECTION_THRESHOLD = config('AI_DETECTION_THRESHOLD', default=70, cast=int)

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND       = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST          = config('EMAIL_HOST',    default='smtp.gmail.com')
EMAIL_PORT          = config('EMAIL_PORT',    default=587, cast=int)
EMAIL_USE_TLS       = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER     = config('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL',  default='ESCEP Niger <noreply@escep.ne>')

# ── Fichiers ──────────────────────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = config('MEDIA_ROOT', default=str(BASE_DIR / 'media'))

DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800

# ── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Africa/Niamey'
USE_I18N = True
USE_TZ   = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTION (Render / serveur)
# ─────────────────────────────────────────────────────────────────────────────
import os
import dj_database_url as _dj_db

# Base de données PostgreSQL via DATABASE_URL (Render)
_db_url = config('DATABASE_URL', default='')
if _db_url:
    DATABASES['default'] = _dj_db.config(
        default=_db_url, conn_max_age=600, ssl_require=True
    )

# Fichiers statiques — WhiteNoise
if not DEBUG:
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
        MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# CSRF — domaines autorisés
_hosts = config('ALLOWED_HOSTS', default='')
if _hosts and not DEBUG:
    CSRF_TRUSTED_ORIGINS = [f"https://{h.strip()}" for h in _hosts.split(',') if h.strip()]

# Cloudinary pour les fichiers media (PDFs, images uploadés)
_cloudinary_name = config('CLOUDINARY_CLOUD_NAME', default='')
if _cloudinary_name:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': _cloudinary_name,
        'API_KEY':    config('CLOUDINARY_API_KEY', default=''),
        'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
    }
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    if 'cloudinary_storage' not in INSTALLED_APPS:
        INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']
