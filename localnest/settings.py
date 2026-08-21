import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1', '.onrender.com']),
)

# Read environment variables from .env file if it exists
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-localnest-development-key-12345')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=True)

ALLOWED_HOSTS = env('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '.onrender.com'])
if isinstance(ALLOWED_HOSTS, str):
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS.split(',') if host.strip()]

# Application definition
INSTALLED_APPS = [
    # Cloudinary storage needs to be before staticfiles if overriding static,
    # but we are using Whitenoise for static and Cloudinary only for media.
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third Party Apps
    'rest_framework',
    'cloudinary_storage',
    'cloudinary',
    
    # Local Apps
    'accounts',
    'hosts',
    'properties',
    'bookings',
    'reviews',
    'payments',
    'dashboard',
    'chat',
    'notifications',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serves static files efficiently in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'localnest.urls'

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
                'notifications.context_processors.unread_notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'localnest.wsgi.application'

# Database
# Use PostgreSQL if DATABASE_URL environment variable is provided, else fallback to SQLite
if env('DATABASE_URL', default=''):
    DATABASES = {
        'default': env.db('DATABASE_URL')
    }
else:
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

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media storage configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary Integration (Only activated if USE_CLOUDINARY=True is explicitly set)
USE_CLOUDINARY = env.bool('USE_CLOUDINARY', default=False)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': env('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY': env('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': env('CLOUDINARY_API_SECRET', default=''),
}

if USE_CLOUDINARY and CLOUDINARY_STORAGE['CLOUD_NAME'] and CLOUDINARY_STORAGE['API_KEY'] and CLOUDINARY_STORAGE['API_SECRET']:
    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    # Use standard FileSystemStorage (served by Whitenoise/Django fallback in production)
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# Authentication URL Redirects
LOGIN_URL = 'accounts:login'
LOGOUT_REDIRECT_URL = 'core:home'
LOGIN_REDIRECT_URL = 'dashboard:dispatcher'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Simulated Email Backend Configuration (Console backend for dev, SMTP ready for production)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = env('EMAIL_PORT', default=587)
    EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
    EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)

DEFAULT_FROM_EMAIL = env('EMAIL_FROM', default='LocalNest <noreply@localnest.com>')

# ── Production Security Settings ──────────────────────────────────────────────
# These are only meaningful in production (DEBUG=False).
# Render terminates SSL at the load balancer, so we trust the X-Forwarded-Proto header.
if not DEBUG:
    # Tell Django to trust Render's HTTPS forwarding header
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Redirect all HTTP → HTTPS
    SECURE_SSL_REDIRECT = True
    # Exempt health check route from SSL redirect so internal Render health checks succeed (HTTP -> 200 OK)
    SECURE_REDIRECT_EXEMPT = [r'^health/$']
    # HSTS: tell browsers to always use HTTPS for 1 year
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Secure cookies (only sent over HTTPS)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# CSRF trusted origins (required for Render + any custom domain)
_csrf_origins = env('CSRF_TRUSTED_ORIGINS', default='')
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]

