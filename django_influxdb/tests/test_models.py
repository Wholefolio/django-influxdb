import unittest
from unittest.mock import patch
from influxdb_client.client.flux_table import FluxRecord, FluxTable

from .mocks import MockInfluxClient, MOCK_RECORD
from django_influxdb.models import InfluxModel
from django.conf import settings


class TestInfluxModel(unittest.TestCase):
    """Test the InfluxModel"""

    def setUp(self):
        self.model = InfluxModel()
        self.model.bucket = settings.INFLUXDB_DEFAULT_BUCKET
        self.model.measurement = "test-model"

    def test_validate_with_data(self):
        """Test validating with data"""
        self.model.field = "price"
        self.model.data = {"price": 123}
        self.model._validate()
        self.assertTrue(self.model.validated_data)

    def test_clean_result(self):
        """Test cleaning a result from unnecessary fields"""
        record = FluxRecord(table=0)
        record.values = {"_value": 123}
        influx_fields = ["_measurement", "_start", "_stop", "result", "table", "_time"]
        for i in influx_fields:
            record.values[i] = True

        result = self.model._clean_result(record)
        for i in influx_fields:
            self.assertFalse(i in result)

    def test_flatten_result(self):
        """Test the flatten results method"""
        tables = []
        for i in range(10):
            t = FluxTable()
            r = FluxRecord(table=0)
            r.values = MOCK_RECORD
            t.records = [r]
            tables.append(
                t
            )
        output = self.model._flatten_results(tables)
        for i in output:
            self.assertFalse(isinstance(i, list))

    @patch("django_influxdb.models.InfluxClient")
    def test_write(self, mock):
        mock.return_value = MockInfluxClient
        self.model.data = MOCK_RECORD
        self.model.field = MOCK_RECORD["_field"]
        self.model.save()
        self.assertTrue(mock.called)
