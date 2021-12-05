invalid_timestamp_msg = "Timestamp is not a valid ISO datetime or InfluxDB relative timestamp"
non_existing_org_msg = "Organization doesn't exist in InfluxDB"


class InfluxApiException(Exception):
    pass


class MissingParametersException(Exception):
    pass


class BadDataType(Exception):
    pass


class NonExistingOrg(Exception):
    def __init__(self, message=non_existing_org_msg):
        self.message = message
        super().__init__(self.message)


class InvalidTimestamp(Exception):
    def __init__(self, message=invalid_timestamp_msg):
        self.message = message
        super().__init__(self.message)
