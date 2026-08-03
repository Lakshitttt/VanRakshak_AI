"""
Satellite provider interface.

Defines the contract every satellite imagery source must implement.
Contains no Sentinel-specific (or any other provider-specific) logic —
that lives in each provider's own module (e.g. sentinel.py). Adding a
future provider (Google Earth Engine, Planet, Mapbox) means writing a
new class that implements `SatelliteProvider`; nothing in
`downloader.py` or the prediction pipeline needs to change.
"""

from abc import ABC, abstractmethod

from app.services.satellite.models import RawSatelliteImage, SatelliteImageRequest


class SatelliteProvider(ABC):
    """Abstract base class for a satellite imagery source."""

    @abstractmethod
    def fetch_image(self, request: SatelliteImageRequest) -> RawSatelliteImage:
        """
        Retrieve raw satellite imagery covering the requested location.

        Args:
            request: The coordinates, buffer, size, and lookback window
                describing the image to retrieve.

        Returns:
            The raw image bytes and retrieval metadata. Implementations
            do not save the image to disk — that is the downloader's
            responsibility.

        Raises:
            SatelliteAuthenticationError: If provider authentication
                fails.
            SatelliteImageRetrievalError: If the image cannot be
                retrieved for any other reason.
        """
        raise NotImplementedError
