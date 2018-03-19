from .base import *

if os.environ.get('DJANGO_LOCAL'):
    CELERY_BROKER_URL = 'redis://localhost:6379'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379'
