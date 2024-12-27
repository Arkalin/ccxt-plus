# custom_exceptions.py
class BaseError(Exception):
    """Base class for all custom exceptions."""

    def __init__(self, message=None, code=None):
        self.message = message or "An error occurred"
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return (
            f"[Error Code: {self.code}] {self.message}" if self.code else self.message
        )


class ConfigurationError(BaseError):
    """Exception raised for errors in configuration."""

    def __init__(self, message=None, code=1001):
        super().__init__(message or "Configuration error occurred", code)


class DataFormatValidationError(BaseError):
    """Exception raised for data format validation errors."""

    def __init__(self, message=None, code=1002):
        super().__init__(message or "Data format validation error occurred", code)


class TaskInitializationError(BaseError):
    """Exception raised for task initialization failures."""

    def __init__(self, message=None, code=1003):
        super().__init__(message or "Task initialization failed", code)


class ExceedMaxMissingPointsError(BaseError):
    """Exception raised for exceeding configured max missing points"""

    def __init__(self, message=None, code=1005):
        super().__init__(message or "Exceeded max missing points", code)
