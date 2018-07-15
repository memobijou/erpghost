web: gunicorn erpghost.wsgi
worker: celery -A erpghost worker -l info
clock: python manage.py online_cronjob
