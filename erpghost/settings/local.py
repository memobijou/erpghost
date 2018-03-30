from .base import *

CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'django-db'


STATIC_URL = '/static/'
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("PG_DB"),
        'USER': os.environ.get("PG_USER"),
        'PASSWORD': os.environ.get("PG_PASSWORD"),
        'HOST': os.environ.get("PG_HOST"),
        'PORT': os.environ.get("PG_PORT"),
    }
}

# import dj_database_url
#
# db_from_env = dj_database_url.config()
# DATABASES['default'].update(db_from_env)