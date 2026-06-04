"""
Custom exception hierarchy for THRESHOLD.

All project-specific errors inherit from ThresholdError, allowing both broad ('catch any THRESHOLD error') and narrow ('catch only this specific type' ) exception handling.
"""


# Base class
class ThresholdError(Exception):
    """Base exception for all THRESHOLD-specific errors."""
    pass


# Validation Errors
class InvalidTravelerError(ThresholdError):
    """Raised when a Traveler is created with invalid data."""
    pass

class InvalidDirectiveError(ThresholdError):
    """Raised when a Directive is created with invalid data."""
    pass

class InvalidQuestionError(ThresholdError):
    """Raised when an interrogation Question is created with invalid data."""
    pass


class CorruptedDataError(ThresholdError):
    """Raised when a saved data file exists but cannot be parsed."""
    pass


# Control-flow signals

class ShiftExpiredError(ThresholdError):
    """Raised when the shift clock runs out mid-action."""
    pass

class ReviewTriggeredError(ThresholdError):
    """Raised when 3 consecutive errors OR 5 total errors occur - Internal affairs itervenes."""
    pass



