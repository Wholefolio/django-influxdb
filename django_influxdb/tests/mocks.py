from influxdb_client.client.flux_table import FluxRecord, FluxTable

MOCK_RECORD = {
    "symbol": "BTC",
    "_field": "price",
    "_value": 25000,
    "price": 25000,
    "_time": True
}


class MockInfluxClient:
    def query(time_start, tags, **kwargs):
        table = FluxTable()
        record = FluxRecord(table=0)
        record.values = MOCK_RECORD
        table.records = [record]
        return [table]

    def write(**kwargs):
        return True
