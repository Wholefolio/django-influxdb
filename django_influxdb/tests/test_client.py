import unittest

from django_influxdb.influxdb import Client


class TestInfluxClient(unittest.TestCase):
    """Test cases for InfluxDB Client"""

    def setUp(self):
        self.client = Client(measurement="test-client")

    def test_init(self):
        """Test proper init"""
        self.assertTrue(isinstance(self.client, Client))


class TestBuildQuery(unittest.TestCase):
    def setUp(self):
        self.client = Client(measurement="test-query")

    def test_no_params(self):
        self.client._build_query()
        assert "from(bucket" in self.client.query
        assert "range" in self.client.query
        assert "_measurement" in self.client.query

    def test_drop_internal_fields(self):
        self.client.drop_internal_fields = True
        self.client._build_query()
        assert "drop" in self.client.query

    def test_sorting_tags(self):
        """Test with sorting tags"""
        self.client.sorting_tags = ["type", "value"]
        self.client._build_query()
        assert "sort" in self.client.query
        for i in self.client.sorting_tags:
            assert i in self.client.query
