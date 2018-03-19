from .base import *

SECRET_KEY = os.environ.get('SECRET_KEY', '9@ytnq8mgd75*q#b+5525)tqq$hk6eia+j*ep&xgykl_#v3=4t')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

CELERY_BROKER_URL = os.environ.get('REDIS_URL')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')

IMPORT_EXPORT_USE_TRANSACTIONS = True

ROOT_URLCONF = 'erpghost.urls'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

import dj_database_url

db_from_env = dj_database_url.config()
DATABASES['default'].update(db_from_env)
# DATABASES['default']['CONN_MAX_AGE'] = 500

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CORS_REPLACE_HTTPS_REFERER = True
HOST_SCHEME = "https://"
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 1000000
SECURE_FRAME_DENY = True
