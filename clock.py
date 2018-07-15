from apscheduler.schedulers.blocking import BlockingScheduler
from online.tasks import mws_task

scheduler = BlockingScheduler()


@scheduler.scheduled_job('interval', seconds=10)
def timed_job():
    print('This job is run every ten seconds.')
    mws_task.delay()
scheduler.start()

