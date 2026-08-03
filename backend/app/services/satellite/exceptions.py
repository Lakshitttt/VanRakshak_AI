"""
Custom exceptions for the satellite subsystem.

All satellite-related errors inherit from `SatelliteError`, which itself
inherits from the application's existing `VanRakshakException` base
(app/core/exceptions.py). This reuses the project's one exception
hierarchy rather than starting a parallel one, and lets the eventual API
layer catch `SatelliteError` (or the base `VanRakshakException`) without
needing to know about provider-specific failure modes.
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


class SatelliteImageRetrievalError(SatelliteError):
    """
    Raised when a satellite provider cannot be reached, or returns an
    error, while retrieving imagery.
    """

    pass


class NoSatelliteImageryAvailableError(SatelliteError):
    """
    Raised when a provider is reachable and authenticated but no
    imagery exists for the requested location and time window.
    """

    pass
