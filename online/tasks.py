from celery import shared_task


@shared_task
def mws_task():
    print("Celery Task has run")