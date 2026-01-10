import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

# Charger les variables d'environnement
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Sécurité
SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS
if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ['notaire-bf-1ns8.onrender.com']

# Applications
INSTALLED_APPS = [
    # Apps Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',

    # Tierces
    'rest_framework',
    'corsheaders',
    'drf_yasg',

    # Applications internes
    'apps.utilisateurs',
    'apps.geographie',
    'apps.notaires',
    'apps.documents',
    'apps.demandes',
    'apps.paiements',
    'apps.actualites',
    'apps.partenaires',
    'apps.conseils',
    'apps.organisation',
    'apps.contact',
    'apps.ventes',
    'apps.stats',
    'apps.communications',
    'apps.audit',
    'apps.system',
    'apps.core',
]

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Toujours en premier
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'notaires_bf.middleware.JWTTokenRefreshMiddleware',
]

ROOT_URLCONF = 'notaires_bf.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'notaires_bf.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Ouagadougou'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static & Media
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Modèle utilisateur
AUTH_USER_MODEL = 'utilisateurs.User'
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3000",
    "https://notaire-bf-1ns8.onrender.com",
    "https://notaire-admin-bf.onrender.com"
]


# CORS
CORS_ALLOW_HEADERS = ['*']
CORS_ALLOW_METHODS = ['*']
CORS_EXPOSE_HEADERS = ["Content-Disposition", "X-Total-Count", "X-Page-Count", "Authorization"]
CORS_ALLOW_ALL_ORIGINS = True

# Sécurité production
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() == 'true'
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'False').lower() == 'true'

SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'

if not DEBUG:
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Emails
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'apikey')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@notaires.bf')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', 'contact@notaires.bf')
EMAIL_TEMPLATE_DIR = BASE_DIR / 'templates/emails'

# SMS
SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'aqilas')  # aqilas, orange, moov, ou autre
# Configuration API Aqilas (SMS universel Burkina Faso)
AQILAS_API_URL = os.getenv('AQILAS_API_URL', 'https://www.aqilas.com/api/v1')
AQILAS_API_KEY = os.getenv('AQILAS_API_KEY', '')
AQILAS_API_SECRET = os.getenv('AQILAS_API_SECRET', '')
AQILAS_SENDER_ID = os.getenv('AQILAS_SENDER_ID', 'ONBF')  # Nom de l'expéditeur
AQILAS_TIMEOUT = int(os.getenv('AQILAS_TIMEOUT', '30'))  # Timeout en secondes

# Variables pour l'envoi d'OTP SMS
AQILAS_TOKEN = os.getenv("AQILAS_TOKEN")
AQILAS_SENDER = os.getenv("AQILAS_SENDER", "ONBF")

ORANGE_API_TOKEN = os.getenv('ORANGE_API_TOKEN', '')
MOOV_API_KEY = os.getenv('MOOV_API_KEY', '')
MOOV_API_SECRET = os.getenv('MOOV_API_SECRET', '')

# Actualités
ACTUALITES_IMAGE_DIR = 'actualites/'
MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']

# Paiements
ORANGE_MONEY_API_URL = os.getenv('ORANGE_MONEY_API_URL', 'https://api.orange.com/orange-money-webpay/bf/v1')
ORANGE_MONEY_API_KEY = os.getenv('ORANGE_MONEY_API_KEY', '')
ORANGE_MONEY_API_SECRET = os.getenv('ORANGE_MONEY_API_SECRET', '')
ORANGE_MONEY_MERCHANT_CODE = os.getenv('ORANGE_MONEY_MERCHANT_CODE', '')
ORANGE_MONEY_CALLBACK_URL = os.getenv('ORANGE_MONEY_CALLBACK_URL', 'https://votre-domaine.com/paiement/callback')

MOOV_MONEY_API_URL = os.getenv('MOOV_MONEY_API_URL', 'https://api.moov-africa.com/bf')
MOOV_MONEY_API_KEY = os.getenv('MOOV_MONEY_API_KEY', '')
MOOV_MONEY_API_SECRET = os.getenv('MOOV_MONEY_API_SECRET', '')
MOOV_MONEY_MERCHANT_ID = os.getenv('MOOV_MONEY_MERCHANT_ID', '')
MOOV_MONEY_CALLBACK_URL = os.getenv('MOOV_MONEY_CALLBACK_URL', 'https://notaire-bf-1ns8.onrender.com/api/auth/paiement/callback')

# Base URL
BASE_URL = os.getenv('BASE_URL', 'https://notaire-bf-1ns8.onrender.com')

# System
SYSTEM_CONFIG = {
    'BACKUP_DIR': '/var/backups/app',
    'ENCRYPTION_KEY': os.getenv('ENCRYPTION_KEY', ''),
    'LOG_RETENTION_DAYS': 90,
    'METRIC_RETENTION_DAYS': 30,
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}