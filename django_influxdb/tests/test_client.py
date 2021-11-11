import unittest
from unittest.case import TestCase

from django_influxdb.influxdb import Client
from django_influxdb import exceptions


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
        self.client.drop_fields = ["test_field"]
        self.client._build_query()
        assert "drop" in self.client.query

    def test_sorting_tags(self):
        """Test with sorting tags"""
        self.client.sorting_tags = ["type", "value"]
        self.client._build_query()
        assert "sort" in self.client.query
        for i in self.client.sorting_tags:
            assert i in self.client.query

    def test_aggregate(self):
        """Test with the aggregate option"""
        self.client.aggregate = ["_time"]
        self.client._build_query()
        assert "aggregateWindow" in self.client.query


class TestCheckTime(TestCase):
    def setUp(self):
        self.client = Client(measurement="test-checktime")

    def test_iso_date(self):
        timestamp = "2021-10-10T14:00"
        res = self.client._check_time(timestamp)
        assert timestamp in res
        assert "time" in res

    def test_bad_date(self):
        timestamp = "2021-48"
        with self.assertRaises(exceptions.InvalidTimestamp):
            self.client._check_time(timestamp)

    def test_influx_relative(self):
        timestamp = "30m"
        res = self.client._check_time(timestamp)
        assert timestamp in res
        assert "-" in res

    def test_bad_relative_timestamp(self):
        timestamp = "40q"
        with self.assertRaises(exceptions.InvalidTimestamp):
            self.client._check_time(timestamp)

    def test_now(self):
        timestamp = "now()"
        res = self.client._check_time(timestamp)
        assert timestamp in res
