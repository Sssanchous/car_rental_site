from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-=$&&-p8gyd!vcwxt+m5v8i+@m6_eo@k6^d9kj)7!vns%os-$6k'

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


# --------------------
#   INSTALLED APPS
# --------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django.contrib.postgres',
    'rental',
]


# --------------------
#     MIDDLEWARE
# --------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',   # обязателен!
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # обязателен!
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'car_rental_site.urls'


# --------------------
#     TEMPLATES
# --------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # твоя папка шаблонов
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',   # обязателен!
                'django.contrib.auth.context_processors.auth',  # обязателен!
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'car_rental_site.wsgi.application'


# --------------------
#     DATABASE
# --------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'car_rental',
        'USER': 'postgres',
        'PASSWORD': '2005',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# --------------------
# PASSWORD VALIDATION
# --------------------
AUTH_PASSWORD_VALIDATORS = []   # ← убрал чтобы не мешало твоему 12345 логину!


# --------------------
#     LOCALE
# --------------------
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'

USE_I18N = True
USE_TZ = False


# --------------------
#     STATIC
# --------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [
     BASE_DIR / 'rental' / 'static',
]


# --------------------
#     SESSIONS — FIX
# --------------------
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 неделя
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"   # <---- если иначе, session НЕ читается


# --------------------
#     CSRF FIX
# --------------------
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = "Lax"


# --------------------
#     LOGIN / LOGOUT
# --------------------
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/clients/"
LOGOUT_REDIRECT_URL = "/login/"

