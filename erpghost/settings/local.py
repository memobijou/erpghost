from .base import *

SECRET_KEY = '9@ytnq8mgd75*q#b+5525)tqq$hk6eia+j*ep&xgykl_#v3=4t'


CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'django-db'


CORS_REPLACE_HTTPS_REFERER = False
HOST_SCHEME = "http://"
SECURE_PROXY_SSL_HEADER = None
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = None
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_FRAME_DENY = False


# DATABASE

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get("PG_DB"),
#         'USER': os.environ.get("PG_USER"),
#         'PASSWORD': os.environ.get("PG_PASSWORD"),
#         'HOST': os.environ.get("PG_HOST"),
#         'PORT': os.environ.get("PG_PORT"),
#     }
# }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': "postgres",
        'USER': "postgres",
        'PASSWORD': "postgres",
        'HOST': "db",
        'PORT': 5432,
    }
}


ALLOWED_HOSTS = ['*']


# DEBUG TOOLBAR

# INTERNAL_IPS = ('127.0.0.1',)
