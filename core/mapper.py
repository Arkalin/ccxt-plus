from errors import DataFormatValidationError


class BaseMapper:
    """
    Base class for data mapper. Only classes inheriting this can be used as mapper in CCXTExchangeWrapper.
    Subclasses must override the `columns` class variable to define their specific structure.
    """

    _validated = False
    columns = None
    time_column_index = 0

    @staticmethod
    def map(data) -> list[list]:
        raise NotImplementedError("Subclasses must implement the map method")

    @classmethod
    def validate(cls, data):
        if not cls._validated:
            if cls.columns is None:
                raise NotImplementedError(
                    "Subclasses must define the `columns` class variable"
                )
            for row in data:
                if len(row) != len(cls.columns):
                    raise DataFormatValidationError(
                        f"Row length {len(row)} does not match expected columns {len(cls.columns)}"
                    )
            cls._validated = True
        return True

    @classmethod
    def map_with_validation(cls, data):
        if not isinstance(data, list):
            raise ValueError(f"Data has a bad type:{type(data)}")
        data = cls.map(data)
        cls.validate(data)
        return data


class OHLCVMapper(BaseMapper):
    columns = ["time", "open", "high", "low", "close"]

    @staticmethod
    def map(data):
        return [entry[:5] for entry in data]


class FundingRateHistoryMapper(BaseMapper):
    columns = ["time", "rate"]

    @staticmethod
    def map(data):
        return [
            [
                item["info"]["fundingTime"],
                item["info"]["fundingRate"],
            ]
            for item in data
        ]
