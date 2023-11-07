from pathlib import Path
from .config import AppConfig

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-7+pi0)&orq-c)01-0vt$^=^jhs-m$)t3b7h-sx!i+#)lwbs^u5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = AppConfig.APP_DEBUG
if DEBUG:
    print('Base dir is \t', BASE_DIR)


ALLOWED_HOSTS = ['app', 'localhost', AppConfig.APP_FRONTEND_HOST]

CSRF_TRUSTED_ORIGINS = [
 'http://localhost', f'http://{AppConfig.APP_FRONTEND_HOST}',
"https://localhost", f"https://{AppConfig.APP_FRONTEND_HOST}"
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
    'bmgt435_elp.middlewares.CORSMiddleware',
    'bmgt435_elp.middlewares.AuthenticationMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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

if AppConfig.APP_USE_MYSQL:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': AppConfig.APP_MYSQL_DB,
            "HOST":AppConfig.APP_MYSQL_HOST,
            "PORT":AppConfig.APP_MYSQL_PORT,
            "USER":AppConfig.APP_MYSQL_USER,
            "PASSWORD":AppConfig.APP_MYSQL_PASSWORD,
            'MYSQL': {
                'driver': 'pymysql',
                'charset': 'utf8mb4',
            },
        },
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
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

STATIC_URL = 'bmgt435-service/static/'

STATIC_ROOT = BASE_DIR.absolute().as_posix() + '/static/'

if DEBUG:
    print('Static root is \t', STATIC_ROOT)

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'