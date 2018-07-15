from celery import shared_task
import mws, os


@shared_task
def mws_task():
    orders_api = mws.Orders(access_key=os.environ.get("MWS_ACCESS_KEY"),
                            secret_key=os.environ.get("MWS_SECRET_KEY"),
                            account_id=os.environ['MWS_ACCOUNT_ID'],
                            region="DE",
                            )
    print(f'Celery Task has run - {orders_api}')
