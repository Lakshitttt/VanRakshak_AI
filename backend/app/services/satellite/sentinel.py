"""
Sentinel Hub satellite provider.

Contains ONLY Sentinel Hub-specific logic: OAuth2 client-credentials
authentication (with token caching), Process API request construction,
and image retrieval. No other module in the satellite subsystem knows
about Sentinel Hub's authentication flow or request format — this is
the sole implementation of `SatelliteProvider` for Sentinel Hub.
"""

import email
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Final, Optional, Tuple

import requests

from app.core.logging import get_logger
from app.core.satellite_settings import satellite_settings
from app.services.satellite.exceptions import (
    SatelliteAuthenticationError,
    SatelliteImageRetrievalError,
)
from app.services.satellite.models import RawSatelliteImage, SatelliteImageRequest
from app.services.satellite.provider import SatelliteProvider

logger = get_logger(__name__)

# --- Sentinel Hub endpoints ---
TOKEN_URL: Final[str] = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)
PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
# --- Request tuning ---
REQUEST_TIMEOUT_SECONDS: Final[int] = 30
TOKEN_EXPIRY_BUFFER_SECONDS: Final[int] = 60
DEFAULT_TOKEN_TTL_SECONDS: Final[int] = 3600

PROVIDER_NAME: Final[str] = "sentinel-hub"

# Sentinel Hub returns this Content-Type for a single-output response;
# used to detect the (already-handled) single-part case below.
SINGLE_PART_CONTENT_TYPE: Final[str] = "image/png"

# True-color Sentinel-2 L2A evalscript (Process API v3). The 2.5x gain
# brightens raw reflectance values into a visually usable true-color
# image — a standard, widely used Sentinel Hub evalscript pattern.
#
# `updateOutputMetadata` records the acquisition date of the scene(s)
# Sentinel Hub selected for the mosaic. Per the Process API spec, the
# resulting "userdata" JSON part is produced automatically from this
# function as long as the request body's `output.responses` includes a
# "userdata" identifier (see _build_process_request_body) — "userdata"
# must NOT also be declared as an output here. Declaring it as a second
# entry in `output` makes Sentinel Hub apply raster sample-type
# validation to it, which fails because application/json supports no
# sample type at all (the exact cause of the "Format application/json
# does not support sample type AUTO" error).
EVALSCRIPT_TRUE_COLOR: Final[
    str
] = """
//VERSION=3
function setup() {
  return {
    input: ["B04", "B03", "B02"],
    output: { bands: 3, sampleType: "AUTO" }
  };
}
function evaluatePixel(sample) {
  return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
}
function updateOutputMetadata(scenes, inputMetadata, outputMetadata) {
  var dates = (scenes.tiles || []).map(function (tile) { return tile.date; });
  outputMetadata.userData = { acquisition_dates: dates };
}
""".strip()


class SentinelProvider(SatelliteProvider):
    """
    Satellite imagery provider backed by the Sentinel Hub Process API.

    Retrieves a Sentinel-2 L2A true-color composite for the requested
    bounding box, using least-cloud-cover mosaicking over the request's
    lookback window so a single call can return a usable image without
    a separate catalog search.
    """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None) -> None:
        """
        Args:
            client_id: Sentinel Hub OAuth2 client ID. Defaults to
                `satellite_settings.SENTINEL_HUB_CLIENT_ID`.
            client_secret: Sentinel Hub OAuth2 client secret. Defaults
                to `satellite_settings.SENTINEL_HUB_CLIENT_SECRET`.
        """
        self._client_id = client_id if client_id is not None else satellite_settings.SENTINEL_HUB_CLIENT_ID
        self._client_secret = (
            client_secret if client_secret is not None else satellite_settings.SENTINEL_HUB_CLIENT_SECRET
        )
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def fetch_image(self, request: SatelliteImageRequest) -> RawSatelliteImage:
        """
        Retrieve a Sentinel-2 L2A true-color image covering the
        requested location.

        Args:
            request: The coordinates, buffer, size, and lookback window
                describing the image to retrieve.

        Returns:
            The raw image bytes and metadata returned by Sentinel Hub.

        Raises:
            SatelliteAuthenticationError: If OAuth2 authentication fails.
            SatelliteImageRetrievalError: If the Process API request
                fails, or the network is unreachable.
        """
        access_token = self._get_access_token()
        request_body = self._build_process_request_body(request)

        try:
            response = requests.post(
                PROCESS_URL,
                json=request_body,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise SatelliteImageRetrievalError(
                "Unable to reach Sentinel Hub while retrieving imagery.",
                details=str(exc),
            ) from exc

        if response.status_code != 200:
            raise SatelliteImageRetrievalError(
                f"Sentinel Hub returned status {response.status_code} while retrieving imagery.",
                details=response.text[:500],
            )

        image_bytes, user_data = self._parse_multipart_response(response)

        if image_bytes is None:
            raise SatelliteImageRetrievalError(
                "Sentinel Hub's response did not include an image.",
                details=response.headers.get("Content-Type"),
            )

        return RawSatelliteImage(
            content=image_bytes,
            content_type=SINGLE_PART_CONTENT_TYPE,
            provider_name=PROVIDER_NAME,
            acquisition_date=self._extract_acquisition_date(user_data),
        )

    @staticmethod
    def _parse_multipart_response(response: requests.Response) -> Tuple[Optional[bytes], Optional[Dict[str, Any]]]:
        """
        Split a Sentinel Hub Process API response into its image bytes
        and (if present) its `userdata.json` metadata part.

        Requesting more than one output (here: the image and a
        `userdata` JSON part) makes Sentinel Hub return a
        `multipart/form-data` response instead of a plain image body.
        Python's stdlib `email` module can parse that format directly
        by treating the response as a MIME message, once its
        Content-Type header is attached to the raw bytes.

        Args:
            response: The raw HTTP response from the Process API.

        Returns:
            A `(image_bytes, user_data)` tuple. Either element may be
            `None` if that part was missing or unparsable.
        """
        content_type = response.headers.get("Content-Type", "")

        if not content_type.startswith("multipart"):
            # A single-output response is just the image body as-is.
            return response.content, None

        mime_message = email.message_from_bytes(
            b"Content-Type: " + content_type.encode("utf-8") + b"\r\nMIME-Version: 1.0\r\n\r\n" + response.content
        )

        image_bytes: Optional[bytes] = None
        user_data: Optional[Dict[str, Any]] = None

        for part in mime_message.walk():
            part_content_type = part.get_content_type()

            if part_content_type == "image/png":
                image_bytes = part.get_payload(decode=True)
            elif part_content_type == "application/json":
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        user_data = json.loads(payload)
                    except (ValueError, TypeError):
                        user_data = None

        return image_bytes, user_data

    @staticmethod
    def _extract_acquisition_date(user_data: Optional[Dict[str, Any]]) -> Optional[datetime]:
        """
        Best-effort extraction of an acquisition date from the
        `userdata.json` part produced by `EVALSCRIPT_TRUE_COLOR`'s
        `updateOutputMetadata` function.

        Returns `None` (rather than raising) if the metadata is
        missing or in an unexpected shape — the acquisition date is
        "if available" information, not required for the image itself
        to be valid.

        Args:
            user_data: The parsed `userdata.json` payload, if any.

        Returns:
            The acquisition date as a timezone-aware datetime, or None.
        """
        if not user_data:
            return None

        try:
            dates = user_data.get("acquisition_dates") or []
            if not dates or not dates[0]:
                return None
            return datetime.fromisoformat(str(dates[0]).replace("Z", "+00:00"))
        except (AttributeError, ValueError, TypeError, IndexError):
            logger.warning("Could not parse an acquisition date from Sentinel Hub's response.")
            return None

    def _get_access_token(self) -> str:
        """
        Return a cached OAuth2 access token, requesting a new one if
        none is cached yet or the cached token is near expiry.

        Returns:
            A valid Sentinel Hub bearer access token.

        Raises:
            SatelliteAuthenticationError: If credentials are missing or
                the token request fails.
        """
        now = time.time()

        if self._access_token and now < (self._token_expires_at - TOKEN_EXPIRY_BUFFER_SECONDS):
            return self._access_token

        if not self._client_id or not self._client_secret:
            raise SatelliteAuthenticationError(
                "Sentinel Hub credentials are not configured. Set "
                "SENTINEL_HUB_CLIENT_ID and SENTINEL_HUB_CLIENT_SECRET."
            )

        try:
            response = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise SatelliteAuthenticationError(
                "Unable to reach Sentinel Hub's authentication service.",
                details=str(exc),
            ) from exc

        if response.status_code != 200:
            raise SatelliteAuthenticationError(
                f"Sentinel Hub authentication failed with status {response.status_code}.",
                details=response.text[:500],
            )

        payload = response.json()
        self._access_token = payload["access_token"]
        self._token_expires_at = now + float(payload.get("expires_in", DEFAULT_TOKEN_TTL_SECONDS))

        logger.info("Obtained new Sentinel Hub access token.")
        return self._access_token

    def _build_process_request_body(self, request: SatelliteImageRequest) -> Dict[str, Any]:
        """
        Build the Sentinel Hub Process API request body for the given
        image request.

        Args:
            request: The coordinates, buffer, size, and lookback window
                describing the image to retrieve.

        Returns:
            The JSON-serializable Process API request body.
        """
        bounding_box = request.bounding_box()
        time_to = datetime.now(timezone.utc)
        time_from = time_to - timedelta(days=request.days_back)

        return {
            "input": {
                "bounds": {
                    "bbox": bounding_box.as_list(),
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": time_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "to": time_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            },
                            "mosaickingOrder": "leastCC",
                        },
                    }
                ],
            },
            "output": {
                "width": request.width_px,
                "height": request.height_px,
                "responses": [
                    {"identifier": "default", "format": {"type": "image/png"}},
                    {"identifier": "userdata", "format": {"type": "application/json"}},
                ],
            },
            "evalscript": EVALSCRIPT_TRUE_COLOR,
        }
