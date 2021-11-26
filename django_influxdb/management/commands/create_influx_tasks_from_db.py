from django.core.management.base import BaseCommand

from django_influxdb.models import InfluxTasks
from django_influxdb.tasks import EveryTask


class Command(BaseCommand):
    help = "Add an exchange for scheduling(must be available in CCXT)."

    def add_arguments(self, parser):
        parser.add_argument("--name", action="store", dest="name",
                            help="name of the influx task")

    def create(self, name):
        return EveryTask(name=name).create_from_db()

    def handle(self, **options):
        qs = InfluxTasks.objects.all()
        if options["name"]:
            qs = qs.filter(name=options["name"])
        for task in qs:
            result = self.create(task.name)
            self.stdout.write(result)
