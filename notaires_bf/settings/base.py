import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']
# Application definition
INSTALLED_APPS = [
   'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
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
'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'notaire_bf'),
        'USER': os.getenv('DB_USER', 'l3'),
        'PASSWORD': os.getenv('DB_PASSWORD', '12345'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}'''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {   
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {   
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {   
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
# REST Framework Configuration
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
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
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
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuration du modèle utilisateur personnalisé
AUTH_USER_MODEL = 'utilisateurs.User'

CORS_ALLOW_ALL_ORIGINS = True   
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',       
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_EXPOSE_HEADERS = [
    'Content-Disposition',
]

# Configuration Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@notaires.bf')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', 'contact@notaires.bf')

# Configuration SMS
SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'orange')  # orange, moov, ou autre
ORANGE_API_TOKEN = os.getenv('ORANGE_API_TOKEN', '')
MOOV_API_KEY = os.getenv('MOOV_API_KEY', '')
MOOV_API_SECRET = os.getenv('MOOV_API_SECRET', '')

# Templates d'emails
EMAIL_TEMPLATE_DIR = BASE_DIR / 'templates/emails'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuration pour les images d'actualités
ACTUALITES_IMAGE_DIR = 'actualites/'
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']

# settings.py

# Configuration Orange Money
ORANGE_MONEY_API_URL = os.getenv('ORANGE_MONEY_API_URL', 'https://api.orange.com/orange-money-webpay/bf/v1')
ORANGE_MONEY_API_KEY = os.getenv('ORANGE_MONEY_API_KEY', '')
ORANGE_MONEY_API_SECRET = os.getenv('ORANGE_MONEY_API_SECRET', '')
ORANGE_MONEY_MERCHANT_CODE = os.getenv('ORANGE_MONEY_MERCHANT_CODE', '')
ORANGE_MONEY_CALLBACK_URL = os.getenv('ORANGE_MONEY_CALLBACK_URL', 'https://votre-domaine.com/paiement/callback')

# Configuration Moov Money
MOOV_MONEY_API_URL = os.getenv('MOOV_MONEY_API_URL', 'https://api.moov-africa.com/bf')
MOOV_MONEY_API_KEY = os.getenv('MOOV_MONEY_API_KEY', '')
MOOV_MONEY_API_SECRET = os.getenv('MOOV_MONEY_API_SECRET', '')
MOOV_MONEY_MERCHANT_ID = os.getenv('MOOV_MONEY_MERCHANT_ID', '')
MOOV_MONEY_CALLBACK_URL = os.getenv('MOOV_MONEY_CALLBACK_URL', 'https://notaire-bf-1ns8.onrender.com/api/auth//paiement/callback')

# URL de base de votre application
BASE_URL = os.getenv('BASE_URL', 'https://notaire-bf-1ns8.onrender.com')

SYSTEM_CONFIG = {
    'BACKUP_DIR': '/var/backups/app',
    'ENCRYPTION_KEY': os.getenv('ENCRYPTION_KEY', ''),  # À stocker dans les variables d'environnement
    'LOG_RETENTION_DAYS': 90,
    'METRIC_RETENTION_DAYS': 30,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
