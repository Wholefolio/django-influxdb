import logging
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger("marketmanager")


class Client:
    """InfluxDB client"""
    def __init__(self, measurement: str, bucket: str = settings.INFLUXDB_DEFAULT_BUCKET,
                 sorting_tags: list = []):
        self.measurement = measurement
        self.client = InfluxDBClient(url=settings.INFLUXDB_URL, token=settings.INFLUXDB_TOKEN, timeout=3000)
        self.bucket = bucket
        self.time_start = "30m"
        self.time_stop = "now()"
        self.drop_internal_fields = False
        self.sorting_tags = sorting_tags
        self.tags = []
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def _build_query(self):
        """Build InfluxDB query"""
        query = f'from(bucket: "{self.bucket}")'
        query += f' |> range(start: -{self.time_start}, stop: {self.time_stop})'
        query += f' |> filter(fn: (r) => (r._measurement == "{self.measurement}"))'
        if self.tags:
            query += ' |> filter(fn: (r) => ('
            tag_queries = []
            for tag, value in self.tags.items():
                tag_queries.append(f'r.{tag} == "{value}"')
            query += '{}))'.format(" and ".join(tag_queries))
        if self.drop_internal_fields:
            query += ' |> drop(columns: ["_start", "_stop"])'
        if self.sorting_tags:
            # Influx doesn't like the single quotes when building the query columns, hence this
            query += ' |> sort(columns: ["{}"])'.format('","'.join(self.sorting_tags))
        self.query = query
        return query

    def write(self, tags: dict, fields: list, timestamp: bool = True):
        """Write a single timeseries point to the InfluxDB"""
        point = Point(self.measurement)
        for tag, value in tags.items():
            point.tag(tag, value)
        for field in fields:
            point.field(field["key"], field["value"])
        if timestamp:
            point.time(timezone.now(), WritePrecision.MS)
        return self.write_api.write(self.bucket, settings.INFLUXDB_ORG, point)

    def query(self, time_start: str, time_stop: str = "now()", tags: list = []):
        """Query the InfluxDB - returns List of InfluxDB tables which contain records"""
        self.tags = tags
        self.time_start = time_start
        self.time_stop = time_stop
        self._build_query()
        logger.debug(f"Running query: \"{self.query}\"")
        return self.client.query_api().query(self.query, org=settings.INFLUXDB_ORG,)
