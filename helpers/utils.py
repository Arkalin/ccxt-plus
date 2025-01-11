import datetime
from enum import Enum

import pytz

from fake_useragent import UserAgent


_TIMEFRAME_MAPPING = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
    "M": 2628000,
}

_UNITS_MAPPING = {
    "s": 1,
    "ms": 1000,
}

class DataFlag(Enum):
    """
    Enumeration for data flags to indicate the success of a request.

    Attributes:
        NORMAL (int): Indicates a successful request.
        ERROR (int): Indicates a failed request.
    """

    NORMAL = 0
    ERROR = 1


class Labels:
    """
    Class for task labeling and folder creation.

    Attributes:
        labels (list): List of labels with '/' replaced by '-'.
    """

    def __init__(self, *labels):
        """
        Initialize the Labels class by replacing '/' with '-' in the provided labels.

        Args:
            labels (str): Arbitrary number of string labels.
        """
        self.labels = [label.replace("/", "-") for label in labels]

    def __str__(self):
        """
        Join all labels with an underscore to form a single string.

        Returns:
            str: Combined label string.
        """
        return "_".join(self.labels)

    def __iter__(self):
        """
        Allow iteration over the labels.

        Yields:
            str: Each label in the list.
        """
        for label in self.labels:
            yield label


def timeframe_to_timestamp(timeframe, unit="ms"):
    """
    Convert a timeframe string to a timestamp value in milliseconds.

    Args:
        timestamp (int): Timestamp in milliseconds.
        unit (int, optional): Conversion unit, default is 'ms' for milliseconds.

    Returns:
        int: Timestamp value in milliseconds.
    """
    rate = _UNITS_MAPPING[unit]
    return _TIMEFRAME_MAPPING[timeframe[-1]] * int(timeframe[:-1]) * rate


def timestamp_to_datetime(timestamp, unit="ms"):
    """
    Convert a timestamp (in milliseconds) to a formatted datetime string.

    Args:
        timestamp (int): Timestamp in milliseconds.
        unit (int, optional): Conversion unit, default is 'ms' for milliseconds.

    Returns:
        str: Formatted datetime string in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    rate = _UNITS_MAPPING[unit]
    timestamp = int(int(timestamp) / rate)
    dt_object = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    return dt_object.strftime("%Y-%m-%d %H:%M:%S")


def datetime_to_timestamp(dt: str | datetime.datetime, rate=1000):
    """
    Convert a formatted datetime string or datetime object to a timestamp (in milliseconds).

    Args:
        dt (str | datetime.datetime): Formatted datetime string or datetime object.
        rate (int, optional): Conversion rate, default is 1000 for milliseconds.

    Returns:
        int: Corresponding timestamp in milliseconds.
    """
    datetime_format = "%Y-%m-%d %H:%M:%S"
    utc_tz = pytz.timezone("UTC")
    dt_object = (
        datetime.datetime.strptime(dt, datetime_format) if isinstance(dt, str) else dt
    )
    dt_object = utc_tz.localize(dt_object)
    timestamp = int(dt_object.timestamp() * rate)
    return timestamp


def get_random_headers():
    """
    Generate random HTTP headers including a random User-Agent.

    Returns:
        dict: Dictionary of HTTP headers.
    """
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    return headers
