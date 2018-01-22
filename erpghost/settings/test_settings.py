# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = '9@ytnq8mgd75*qasdfs3243#b+5525)tqq$h23432fdafk6eia+j*ep&xgykl_#v3=4t'

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
