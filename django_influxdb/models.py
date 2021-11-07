from functools import reduce
import logging
from django_influxdb.influxdb import Client as InfluxClient

logger = logging.getLogger()


class InfluxModel:
    """Influx Base Model - concept was taken from Django ORM models"""
    required_influx_tags = []
    optional_influx_tags = []
    fields = []

    def __init__(self, **kwargs):
        self.data = kwargs.get("data", {})
        self.validated_data = {"tags": {}, "fields": []}
        self.influx_tags = self.required_influx_tags + self.optional_influx_tags

    def _generate_tags(self, exc_on_missing: bool = True) -> dict:
        """Generate a dictionary of tag->value pairs from a list of tags and a data dict"""
        output = {}
        for key in self.influx_tags:
            if exc_on_missing and key not in self.data and key in self.required_influx_tags:
                raise KeyError(f"Missing required tag {key} from model data")
            elif key in self.optional_influx_tags and key not in self.data:
                continue
            output[key] = self.data[key]
        self.validated_data["tags"] = output
        return output

    def _generate_fields(self) -> dict:
        """Generate the fields """
        for field_dict in self.fields:
            if "name" not in field_dict or "type" not in field_dict:
                raise KeyError('Fields must be declared as a dict: {"name": "field_name", "type": "float"}')
            field_name = field_dict["name"]
            field_type = field_dict["type"]
            if field_name not in self.data:
                raise KeyError(f"Setting the field is mandatory. Missing field: {self.field}")
            value = self.data[field_name]
            # Add the casted value to the list of fields
            field = {"key": field_name, "value": field_type(value)}
            self.validated_data["fields"].append(field)

    def _validate(self) -> None:
        """Validate the tags and fields in the class are present in the data"""
        logger.debug(f"Starting validation for {self.data}")
        self._generate_tags()
        self._generate_fields()
        logger.debug(f"Finished validation. Validated data: {self.validated_data}")

    def _clean_result(self, result):
        """Clean out InfluxDB internal fields and tags and leave only the model tags"""
        current = result.values
        output = {}
        try:
            output["timestamp"] = current["_time"]
        except KeyError:
            pass
        for tag in self.influx_tags:
            if tag not in current:
                continue
            output[tag] = current[tag]
        try:
            output[current["_field"]] = current["_value"]
        except KeyError:
            pass
        return output

    def _flatten_results(self, data):
        """Influx returns the records as a list of tables, which have lists of results.
        Flatten the results to a simple list of results."""
        def red(a, b):
            """Reducer function to flatten the list of table records"""
            if type(a) == list:
                return a + b.records
            return a.records + b.records
        if not data:
            return []
        self.results = reduce(red, data)
        return self.results

    def clean_results(self):
        """Clean each of the results in the list"""
        output = []
        for result in self.results:
            output.append(self._clean_result(result))
        self.results = output
        return self.results

    def filter(self, time_start: str, time_stop: str = "now()"):
        """Query Influx based on the tags from the object (the object must be initialized with the tags)."""
        client = InfluxClient(measurement=self.measurement, sorting_tags=self.sorting_tags)
        tags = self._generate_tags()
        tables = client.query(time_start=time_start, time_stop=time_stop, tags=tags)
        if not tables:
            return []
        self._flatten_results(tables)
        self.clean_results()
        return self.results

    def save(self):
        """Creates a new timeseries entry in Influx from this object"""
        self._validate()
        client = InfluxClient(self.measurement)
        result = client.write(**self.validated_data)
        return result
