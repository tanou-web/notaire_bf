import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

# Charger les variables d'environnement
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'test-secret-key')
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',

    # Applications tierces
    'rest_framework',
    'corsheaders',
    'drf_yasg',

    # Vos applications
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

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

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

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Ouagadougou'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTH_USER_MODEL = 'utilisateurs.User'

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Email actif pour test
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.mailtrap.io')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'test_user')  # Mailtrap user
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'test_pass')  # Mailtrap pass
DEFAULT_FROM_EMAIL = 'noreply@test.local'
CONTACT_EMAIL = 'contact@test.local'

# SMS actif pour test
SMS_PROVIDER = 'aqilas'
AQILAS_API_URL = 'https://www.aqilas.com/api/v1'
AQILAS_API_KEY = 'test_aqilas_key'
AQILAS_API_SECRET = 'test_aqilas_secret'
AQILAS_SENDER_ID = 'TESTAPP'
AQILAS_TIMEOUT = 30

# Paiements actifs pour test (callback fictif)
ORANGE_MONEY_CALLBACK_URL = 'http://127.0.0.1:8000/api/paiement/orange/callback'
MOOV_MONEY_CALLBACK_URL = 'http://127.0.0.1:8000/api/paiement/moov/callback'

BASE_URL = 'http://127.0.0.1:8000'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler',}},
    'root': {'handlers': ['console'], 'level': 'INFO',},
}

ACTUALITES_IMAGE_DIR = 'actualites/'
MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']

SYSTEM_CONFIG = {
    'BACKUP_DIR': '/var/backups/app',
    'ENCRYPTION_KEY': 'test_encryption_key',
    'LOG_RETENTION_DAYS': 90,
    'METRIC_RETENTION_DAYS': 30,
}
