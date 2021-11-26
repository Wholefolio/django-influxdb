from django.core import exceptions
from influxdb_client import InfluxDBClient, Task
from influxdb_client.rest import ApiException
from django.conf import settings
# from django_influxdb.influxdb import Client
from jinja2 import Environment, FileSystemLoader

from django_influxdb.models import InfluxTasks


class BaseTask:
    def _get_org(self) -> str:
        org_api = self.client.organizations_api()
        orgs = org_api.find_organizations()
        for o in orgs:
            if o.name == settings.INFLUXDB_ORG:
                return o
        raise exceptions.NonExistingOrg()

    def _get_influx_task(self) -> Task:
        """Get an existing task by filtering on self.name"""
        if hasattr(self, "task_id"):
            try:
                return self.task_api.find_task_by_id(self.task_id)
            except ApiException:
                # Not found by id - try
                pass
        # Currently the influxdb_client doesn't support filtering by name, only task_id
        for i in self.task_api.find_tasks():
            # There can be more than 1 task with this name so we just return the first one
            if i.name == self.name:
                return i

    def _get_or_create_destination_bucket(self, name):
        if not self.buckets_api.find_bucket_by_name(name):
            org_id = self._get_org().id
            self.buckets_api.create_bucket(bucket_name=name, org_id=org_id)


class EveryTask(BaseTask):
    """Influx task based on Jinja file templates"""
    flux_template_folder = "flux"
    flux_template = "downsampling.j2"

    def __init__(self, name, **kwargs):
        self.name = name
        self.source_bucket = kwargs.get("source_bucket", settings.INFLUXDB_DEFAULT_BUCKET)
        self.__dict__ = {**kwargs, **self.__dict__}
        self.client = InfluxDBClient(url=settings.INFLUXDB_URL, token=settings.INFLUXDB_TOKEN, timeout=3000)
        self.task_api = self.client.tasks_api()
        self.buckets_api = self.client.buckets_api()

    def load_template(self) -> str:
        """Load and render the template with the values"""
        env = Environment(loader=FileSystemLoader(self.flux_template_folder))
        template = env.get_template(self.flux_template)
        return template.render(org=settings.INFLUXDB_ORG, **self.__dict__)

    def get_from_db(self) -> InfluxTasks:
        return InfluxTasks.objects.get(name=self.name)

    def update_from_template(self):
        """Update an existing task from a Jinja2 template."""
        task = self._get_influx_task()
        if task:
            flux = self.load_template()
            task.every = self.task_interval
            task.flux = flux
            self.task_api.update_task(task)
            return task

    def update_from_db(self):
        """Update an existing task from a DB entry"""
        try:
            task = InfluxTasks.objects.get(name=self.name)
            influx_task = self._get_influx_task(task.name)
            if not influx_task:
                return self.create_from_db()
            influx_task.every = task.task_interval
            influx_task.flux = task.flux
            self.task_api.update_task(influx_task)
            return influx_task
        except InfluxTasks.DoesNotExist:
            pass

    def create_from_template(self, filter: str, task_interval: str, time_start: str, destination_bucket: str) -> str:
        """Create a new InfluxDB task from a Jinja2 template from the filesystem."""
        self.filter = filter
        self.task_interval = task_interval
        self.time_start = time_start
        self.destination_bucket = destination_bucket
        if self._get_influx_task():
            raise exceptions.TaskExists()
        self._get_or_create_destination_bucket(destination_bucket)
        flux = self.load_template()
        org = self._get_org()
        return self.task_api.create_task_every(self.name, flux, self.task_interval, organization=org)

    def create_from_db(self) -> str:
        """Create a new InfluxDB task from an existing InfluxTask DB entry"""
        db_obj = self.get_from_db()
        org = self._get_org()
        self._get_or_create_destination_bucket(db_obj.destination_bucket)
        return self.task_api.create_task_every(db_obj.name, db_obj.flux, db_obj.task_interval, organization=org)

    @classmethod
    def run_task(self, name):
        self.name = name
        task = self._get_influx_task()
        return self.task_api.run_manually(task.task_id)
