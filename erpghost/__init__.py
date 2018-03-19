import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erpghost.settings')

app = Celery('erpghost')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.update(BROKER_URL=os.environ.get('REDIS_URL'),
                CELERY_RESULT_BACKEND=os.environ.get('REDIS_URL'))
app.autodiscover_tasks()