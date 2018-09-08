from django.core.management import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from online.tasks import online_task


# The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    # Show this when the user types help
    help = "My test command"

    # A command must define handle()
    def handle(self, *args, **options):
        scheduler = BlockingScheduler()

        @scheduler.scheduled_job('interval', minutes=1)
        def timed_job():
            print('This job is run every 1 minutes.')
            online_task.delay()

        scheduler.start()
        self.stdout.write("Doing All The Things!")
