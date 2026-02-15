import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR est maintenant la racine du projet (là où se trouve manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Chargement explicite du fichier .env (à la racine)
load_dotenv(BASE_DIR / '.env')
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['burkinanotaires.com', 'www.burkinanotaires.com', '76.13.55.146', 'localhost', '127.0.0.1']
#ALLOWED_HOSTS = ['*']
#ALLOWED_HOSTS = ['notaire-bf-1ns8.onrender.com', 'localhost', '127.0.0.1','3001', '0.0.0.0']
'''if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ['notaire-bf-1ns8.onrender.com']
'''
'''# Configuration sécurisée des hôtes autorisés
ALLOWED_HOSTS_ENV = os.getenv('ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(',') if host.strip()]
else:
    # En développement uniquement
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0'] if not DEBUG else ['*']
'''
# Applicati'on definition
INSTALLED_APPS = [
   'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'adminsortable2',
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
    'apps.evenements',
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
# Database
# On utilise PostgreSQL si les variables d'environnement sont définies.
DB_NAME = os.getenv('DB_NAME')
if DB_NAME:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': os.getenv('DB_USER', 'notaire'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'notaire'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    if not DEBUG:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("DB_NAME manquant dans le fichier .env. Le fallback vers SQLite est interdit en production pour éviter les pertes de données.")
    
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
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),  # Augmenté à 2 heures
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Augmenté à 7 jours
    'ROTATE_REFRESH_TOKENS': True,  # Rotation automatique des refresh tokens
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
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = [
    BASE_DIR / 'notaires_bf/static',
]
# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuration du modèle utilisateur personnalisé
AUTH_USER_MODEL = 'utilisateurs.User'
# Configuration CORS flexible
# settings.py


# ===== CORS =====
if DEBUG:
    CORS_ALLOWED_ORIGINS = [

        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3005",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3005",
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        "https://burkinanotaires.com",
        "https://www.burkinanotaires.com",
        "https://notaire-bf-1ns8.onrender.com",
        "https://notaire-admin-bf.onrender.com",
        "https://notaire-bf.onrender.com",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3005",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3005",
    ]

CORS_ALLOW_ALL_ORIGINS = False  # REMETTRE A False pour la production
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-api-key",
    "cache-control",
]


# Configurations de sécurité pour la production
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() == 'true'
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'False').lower() == 'true'

SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'

# Sécuriser les cookies en production
if not DEBUG:
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Configuration Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Configuration SendGrid (RECOMMANDÉ pour DigitalOcean)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'apikey')  # Toujours 'apikey' pour SendGrid
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')  # Votre clé API SendGrid
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@notaires.bf')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', 'contact@notaires.bf')

# Configuration alternative cPanel (si vous utilisez un autre hébergeur)
# EMAIL_HOST = os.getenv('EMAIL_HOST', 'mail.notaires.bf')
# EMAIL_PORT = int(os.getenv('EMAIL_PORT', 465))
# EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False').lower() == 'true'
# EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True').lower() == 'true'
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'noreply@notaires.bf')
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Configuration SMS
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




# Anciennes configurations (maintenues pour compatibilité)
ORANGE_API_TOKEN = os.getenv('ORANGE_API_TOKEN', '')
MOOV_API_KEY = os.getenv('MOOV_API_KEY', '')
MOOV_API_SECRET = os.getenv('MOOV_API_SECRET', '')

# Templates d'emails
EMAIL_TEMPLATE_DIR = BASE_DIR / 'templates/emails'

# Configuration des médias
if not DEBUG:
    # Choix du fournisseur de stockage cloud
    STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 's3')  # 's3' ou 'cloudinary'

    if STORAGE_PROVIDER == 'cloudinary':
        # Configuration Cloudinary (plus simple)
        import cloudinary
        import cloudinary.uploader
        import cloudinary.api

        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
            'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
            'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
        }

        cloudinary.config(**CLOUDINARY_STORAGE)

        CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')
        if CLOUDINARY_URL:
            cloudinary.config_from_url(CLOUDINARY_URL)

        MEDIA_URL = f"https://res.cloudinary.com/{CLOUDINARY_STORAGE['CLOUD_NAME']}/image/upload/"
        DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

    else:
        # Configuration pour la production - AWS S3
        AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            print("WARNING: AWS Keys missing in production mode. Fallback to local storage to prevent crash.")
            MEDIA_URL = '/media/'
            MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
            STATIC_URL = '/static/'
            STATIC_ROOT = BASE_DIR / 'static'
        else:
            AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
            AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'eu-west-1')
            AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')  # Pour DigitalOcean Spaces
            AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN', f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com')
            AWS_DEFAULT_ACL = 'public-read'
            AWS_S3_OBJECT_PARAMETERS = {
                'CacheControl': 'max-age=86400',
            }
            AWS_LOCATION = 'media'

            # Configuration des médias pour S3
            if AWS_S3_CUSTOM_DOMAIN:
                MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
            else:
                MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{AWS_LOCATION}/'

            # Configuration django-storages
            STORAGES = {
                "default": {
                    "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
                },
                "staticfiles": {
                    "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
                },
            }


else:
    # Configuration pour le développement - stockage local
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    STATIC_URL = '/static/'
    # STATICFILES_DIRS = [BASE_DIR / 'static']  # Supprimé car le dossier n'existe pas
    STATIC_ROOT = BASE_DIR / 'static'

# Configuration pour les images d'actualités
ACTUALITES_IMAGE_DIR = 'actualites/'
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']

# settings.py

# Configuration Yengapay
YENGAPAY_API_KEY = os.getenv('YENGAPAY_API_KEY', 'ULmsHRgiSd5WQ6it52ZQr00zlKvefaeg')
YENGAPAY_ORGANIZATION_ID = os.getenv('YENGAPAY_ORGANIZATION_ID', '')
YENGAPAY_PROJECT_ID = os.getenv('YENGAPAY_PROJECT_ID', '77423')
YENGAPAY_WEBHOOK_SECRET = os.getenv('YENGAPAY_WEBHOOK_SECRET', 'e6282d55-a72d-421e-a844-99caa8a3b091')
YENGAPAY_API_URL = os.getenv('YENGAPAY_API_URL', 'https://api.yengapay.com/api/v1')

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








