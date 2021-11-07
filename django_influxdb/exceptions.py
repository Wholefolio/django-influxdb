invalid_timestamp_msg = "Timestamp is not a valid ISO datetime or InfluxDB relative timestamp"


class MissingParametersException(Exception):
    pass


class InvalidTimestamp(Exception):
    def __init__(self, message=invalid_timestamp_msg):
        self.message = message
        super().__init__(self.message)
