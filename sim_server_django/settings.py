"""
Django settings for sim_server_django project.

"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-7+pi0)&orq-c)01-0vt$^=^jhs-m$)t3b7h-sx!i+#)lwbs^u5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("BMGT435_DEBUG", False)
if DEBUG:
    print('Base dir is \t', BASE_DIR)


INDEX_HOST = os.environ.get("BMGT435_INDEX")    # host name of the frontend
ALLOWED_HOSTS = ['app', '127.0.0.1', 'localhost', INDEX_HOST]
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1','http://localhost', f'http://{INDEX_HOST}',
    "https://127.0.0.1", "https://localhost", f"https://{INDEX_HOST}"
]


# Application definition
INSTALLED_APPS = [
    "bmgt435_elp.apps.BmgtPlatformConfig",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'bmgt435_elp.middlewares.bgmt435Middlewares.CORSMiddleware',
    'bmgt435_elp.middlewares.bgmt435Middlewares.AuthenticationMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'bmgt435_elp.middlewares.bgmt435Middlewares.TestModeMiddleware',
]

ROOT_URLCONF = 'sim_server_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [],
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

WSGI_APPLICATION = 'sim_server_django.wsgi.application'
ASGI_APPLICATION = 'sim_server_django.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# DATABASE_ROUTERS = ['bmgt435_elp.utils.databaseUtils.BMGT435_DB_Router', ]

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     },
    # 'analytics': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'analytics.sqlite3',
    # }
# }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get("BMGT435_MYSQL_DB"),
        "HOST":os.environ.get("BMGT435_MYSQL_HOST"),
        "PORT":3306,
        "USER":os.environ.get("BMGT435_MYSQL_USER"),
        "PASSWORD":os.environ.get("BMGT435_MYSQL_PASSWORD"),
        'MYSQL': {
            'driver': 'pymysql',
            'charset': 'utf8mb4',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    # "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    # "django.contrib.auth.hashers.Argon2PasswordHasher",
    # "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = False

USE_TZ = True

STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR.absolute().as_posix() + '/static/'

if DEBUG:
    print('Static root is \t', STATIC_ROOT)

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
