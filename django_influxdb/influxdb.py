import logging
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.rest import ApiException
from django.utils import timezone
from django.conf import settings
from dateutil import parser
from . import exceptions
logger = logging.getLogger("marketmanager")


class Client:
    """InfluxDB client"""
    def __init__(self, measurement: str, bucket: str = settings.INFLUXDB_DEFAULT_BUCKET,
                 drop_fields: list = [], sorting_tags: list = []):
        self.measurement = measurement
        defaults = {"INFLUXDB_TIMEOUT": 3000, "INFLUXDB_BATCH_SIZE": 500, "INFLUXDB_FLUSH_SIZE": 100}
        for key in defaults:
            value = defaults[key]
            if hasattr(settings, key):
                value = getattr(settings, key)
            setattr(self, key, value)
        self.client = InfluxDBClient(url=settings.INFLUXDB_URL, token=settings.INFLUXDB_TOKEN,
                                     timeout=self.INFLUXDB_TIMEOUT)
        self.bucket = bucket
        self.time_start = "30m"
        self.time_stop = "now()"
        # Drop fields can be used before aggregations to join multiple InfluxDB tables
        # that differentiate on those fields
        self.drop_fields = drop_fields
        self.sorting_tags = sorting_tags
        self.tags = []

    @classmethod
    def _check_write_item(cls, item) -> bool:
        if "fields" not in item or "tags" not in item:
            return False
        return True

    @classmethod
    def _check_time(cls, timestamp: str) -> str:
        """Verify the start and stop times are in the proper format"""
        if timestamp == "now()":
            return timestamp
        try:
            # Try parsing it as an ISO timestamp
            parser.isoparse(timestamp)
            # Pass the timestamp string to the Influx time function
            return "time(v: \"{}\")".format(timestamp)
        except ValueError:
            # Timestamp is not a ISO timestamp, check if it's a InfluxDB supported relative time
            if timestamp[-1] not in ["s", "m", "h", "d", "w", "y"] and timestamp[-2:] != "mo":
                raise exceptions.InvalidTimestamp()
            if timestamp[0] == "-":
                return timestamp
            return "-{}".format(timestamp)

    def _build_query(self) -> str:
        """Build InfluxDB query"""
        query = f'from(bucket: "{self.bucket}")'
        query += f' |> range(start: {self.time_start}, stop: {self.time_stop})'
        query += f' |> filter(fn: (r) => (r._measurement == "{self.measurement}"))'
        if self.tags:
            query += ' |> filter(fn: (r) => ('
            tag_queries = []
            for tag, value in self.tags.items():
                if isinstance(value, list):
                    tmp = []
                    for v in value:
                        tmp.append(f'r.{tag} == "{v}"')
                    tag_queries.append(" or ".join(tmp))
                else:
                    tag_queries.append(f'r.{tag} == "{value}"')
            query += '{}))'.format(" and ".join(tag_queries))
        if self.drop_fields:
            query += ' |> drop(columns: ["{}"])'.format('","'.join(self.drop_fields))
        if hasattr(self, "aggregate"):
            query += f' |> aggregateWindow(every: {self.aggregate}, fn: mean, createEmpty: false)'
        if self.sorting_tags:
            # Influx doesn't like the single quotes when building the query columns, hence this
            query += ' |> sort(columns: ["{}"])'.format('","'.join(self.sorting_tags))
        if self.pivot_tables:
            query += ' |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'
        self.query = query
        return query

    def prepare_point(self, tags: dict, fields: dict, timestamp: bool = True):
        """Prepare an Influx point give the tags and fields"""
        point = Point(self.measurement)
        for tag, value in tags.items():
            point.tag(tag, value)
        for field, value in fields.items():
            point.field(field, value)
        if timestamp:
            point.time(timezone.now(), WritePrecision.MS)
        return point

    def write(self, data, timestamp: bool = True):
        """Write timeseries points to the InfluxDB. Data item structure:
        {"tags": {"tag1": "value1"}, "fields": {"value": 15}}
        Each list entry must have a tags and fields key
        """
        points = []
        for item in data:
            if not self._check_write_item(item):
                continue
            points.append(self.prepare_point(item["tags"], item["fields"], timestamp))
        with self.client.write_api() as write_api:
            write_api.write(self.bucket, settings.INFLUXDB_ORG, points)

    def query(self, time_start: str, time_stop: str = "now()", tags: list = [], aggregate: str = None,
              pivot_tables: bool = False):
        """Query the InfluxDB - returns List of InfluxDB tables which contain records"""
        self.tags = tags
        self.time_start = self._check_time(time_start)
        self.time_stop = self._check_time(time_stop)
        self.aggregate = aggregate
        self.pivot_tables = pivot_tables
        self._build_query()
        logger.debug(f"Running query: \"{self.query}\"")
        try:
            return self.client.query_api().query(self.query, org=settings.INFLUXDB_ORG,)
        except ApiException as e:
            raise exceptions.InfluxApiException(e)
