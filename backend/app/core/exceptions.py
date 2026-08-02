"""
Custom exception hierarchy for the VanRakshak AI backend.

Defines the base exception type that all application-specific exceptions
should inherit from. Kept intentionally minimal in this foundation task;
feature-specific exceptions (e.g. invalid image, model load failure) will
be added alongside the features that raise them.
"""

from typing import Any, Optional


class VanRakshakException(Exception):
    """
    Base exception for all VanRakshak AI application errors.

    Every custom exception raised anywhere in the backend should inherit
    from this class so that a single global exception handler (registered
    in app/main.py) can catch and format all of them consistently.
    """

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        """
        Args:
            message: Human-readable error message.
            details: Optional additional context about the error.
        """
        self.message = message
        self.details = details
        super().__init__(message)


class ConfigurationError(VanRakshakException):
    """
    Raised when application configuration is missing or invalid.

    Examples include a required environment variable being absent, or a
    configured value failing validation during application startup.
    """

    pass