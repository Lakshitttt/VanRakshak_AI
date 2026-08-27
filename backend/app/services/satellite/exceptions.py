"""
Custom exceptions for the satellite subsystem.

All satellite-related errors inherit from `SatelliteError`, which itself
inherits from the application's existing `VanRakshakException` base
(app/core/exceptions.py).

This allows the API layer to distinguish between different satellite
failure modes and return useful error messages/status codes.
"""

from app.core.exceptions import VanRakshakException


class SatelliteError(VanRakshakException):
    """Base exception for all satellite retrieval failures."""

    pass


class SatelliteAuthenticationError(SatelliteError):
    """
    Raised when a satellite provider's authentication fails — missing,
    invalid, or expired credentials that a retry cannot fix.
    """

    pass


class SatelliteQuotaError(SatelliteError):
    """
    Raised when the satellite provider rejects a request because the
    account has exhausted its available requests or processing units.
    """

    pass


class SatelliteNetworkError(SatelliteError):
    """
    Raised when the satellite provider cannot be reached because of a
    network, connection, DNS, or timeout problem.
    """

    pass


class SatelliteServiceError(SatelliteError):
    """
    Raised when the satellite provider is reachable but returns a
    server-side error.
    """

    pass


class SatelliteImageRetrievalError(SatelliteError):
    """
    Raised when a satellite provider returns an error while retrieving
    imagery that does not fit a more specific satellite error category.
    """

    pass


class NoSatelliteImageryAvailableError(SatelliteError):
    """
    Raised when a provider is reachable and authenticated but no
    imagery exists for the requested location and time window.
    """

    pass