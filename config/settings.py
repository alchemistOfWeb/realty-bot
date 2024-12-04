"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 5.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# third-party modules
import os
from dotenv import dotenv_values, load_dotenv
import psycopg2


if os.getenv("RAILWAY_ENVIRONMENT") is None:  # Railway добавляет эту переменную автоматически
    load_dotenv()






# config = dotenv_values('.env')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-14b3qm-zaklufap*kz=%8b!4_p)9bcm$dvj--)los4iu3nwydx'
# SECRET_KEY = config.get('SECRET_KEY', 'your-default-secret-key')
SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = config.get('DEBUG', '0') == '1'
DEBUG = os.getenv("DEBUG", "0") == "1"
# DEBUG = True

# ALLOWED_HOSTS = config.get("DJANGO_ALLOWED_HOSTS", "localhost").split(" ")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost").split()

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'botmodels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'



# Celery
# https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html
# CELERY_RESULT_BACKEND = 'django-db'
# CELERY_CACHE_BACKEND = 'default'


# CELERY_BROKER_URL = config.get("CELERY_BROKER_URL", 'redis://redis:6379/0')
REDIS_URL = os.getenv("CELERY_BROKER_URL", 'redis://redis:6379')
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL + '/0')
# CELERY_RESULT_BACKEND = config.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL + '/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'



# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases



# DATABASE_HOST = config.get('POSTGRES_HOST', 'db')
DATABASE_HOST = os.getenv("POSTGRES_HOST", "localhost")
# DATABASE_PORT = config.get('POSTGRES_PORT', '5432')
DATABASE_PORT = os.getenv("POSTGRES_PORT", "5432")

# DATABASE_NAME = config.get('POSTGRES_DB')
DATABASE_NAME = os.getenv("POSTGRES_DB")

# DATABASE_USER = config.get('POSTGRES_USER')
DATABASE_USER = os.getenv("POSTGRES_USER")

# DATABASE_PASSWORD = config.get('POSTGRES_PASSWORD', "django_password")
DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD")

DEV_WITHOUT_DOCKER = os.getenv("DEV_WITHOUT_DOCKER", "True") == "True"

if not DEV_WITHOUT_DOCKER:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DATABASE_NAME,
            'USER': DATABASE_USER,
            'PASSWORD': DATABASE_PASSWORD,
            'HOST': DATABASE_HOST,
            'PORT': DATABASE_PORT,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': "db.sqlite3"
        }
    }

CACHE_LOCATION = f"{REDIS_URL}/1" # TODO: think it over

if not DEV_WITHOUT_DOCKER:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': CACHE_LOCATION,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'TIMEOUT': None,
        }
    }



# Telegram bot api settings
BOT_API_TOKEN = os.getenv("BOT_API_TOKEN")

# takes MINUTES:SECONDS
BOT_DEFAULT_COUNTDOWN = os.getenv("BOT_DEFAULT_COUNTDOWN", "3:00")

# takes HOUR:MINUTE
BOT_START_SENDING_TIME = os.getenv("BOT_START_SENDING_TIME", "8:00")
BOT_END_SENDING_TIME = os.getenv("BOT_END_SENDING_TIME", "23:00")


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

