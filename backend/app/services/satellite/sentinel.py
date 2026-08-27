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
    SatelliteNetworkError,
    SatelliteQuotaError,
    SatelliteServiceError,
)
from app.services.satellite.models import RawSatelliteImage, SatelliteImageRequest
from app.services.satellite.provider import SatelliteProvider

from app.services.satellite.catalog import find_best_scene, CatalogScene

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
SINGLE_PART_CONTENT_TYPE: Final[str] = "image/png"

# --- Cloud-Masking & Median Compositing Evalscript ---
EVALSCRIPT_TRUE_COLOR: Final[
    str
] = """
//VERSION=3
function setup() {
  return {
    input: ["B04", "B03", "B02", "SCL", "dataMask"],
    output: { bands: 3, sampleType: "AUTO" },
    mosaicking: "ORBIT"
  };
}

function evaluatePixel(samples) {
  var clearPixels = [];
  
  for (var i = 0; i < samples.length; i++) {
    var sample = samples[i];
    var isCloud = (sample.SCL === 3 || sample.SCL === 8 || sample.SCL === 9 || sample.SCL === 10);
    
    if (sample.dataMask === 1 && !isCloud) {
      clearPixels.push(sample);
    }
  }

  // Fallback: If all available pixels over this spot are cloudy, return the first one 
  // to prevent returning a black array to ResNet.
  if (clearPixels.length === 0) {
     return [2.5 * samples[0].B04, 2.5 * samples[0].B03, 2.5 * samples[0].B02];
  }

  clearPixels.sort(function(a, b) { return a.B04 - b.B04; });
  var medianIndex = Math.floor(clearPixels.length / 2);
  var medianPixel = clearPixels[medianIndex];

  return [2.5 * medianPixel.B04, 2.5 * medianPixel.B03, 2.5 * medianPixel.B02];
}

function updateOutputMetadata(scenes, inputMetadata, outputMetadata) {
  var dates = (scenes.orbits || []).map(function (orbit) { return orbit.dateFrom; });
  outputMetadata.userData = { acquisition_dates: dates };
}
""".strip()

class SentinelProvider(SatelliteProvider):
    """
    Satellite imagery provider backed by the Sentinel Hub Process API.
    """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None) -> None:
        self._client_id = client_id if client_id is not None else satellite_settings.SENTINEL_HUB_CLIENT_ID
        self._client_secret = (
            client_secret if client_secret is not None else satellite_settings.SENTINEL_HUB_CLIENT_SECRET
        )
        
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def fetch_image(self, request: SatelliteImageRequest) -> RawSatelliteImage:
        """
        Retrieve a Sentinel-2 L2A true-color image covering the requested location.
        """
        access_token = self._get_access_token()
        
        time_to = datetime.now(timezone.utc)
        # Force a 90-day search window to ensure we always get a scene, even in monsoon season
        time_from = time_to - timedelta(days=90)
        
        best_scene = find_best_scene(
            access_token=access_token,
            bbox=request.bounding_box().as_list(),
            time_from=time_from,
            time_to=time_to
        )
        
        if not best_scene:
            raise SatelliteImageRetrievalError(
                "No suitable imagery found in the 90-day search window."
            )

        request_body = self._build_process_request_body(request, best_scene)

        try:
            response = requests.post(
                PROCESS_URL,
                json=request_body,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "multipart/mixed"  # Prevents .tar payload bugs
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise SatelliteNetworkError(
                "Unable to reach Sentinel Hub while retrieving imagery. "
                "Please check your internet connection and try again.",
                details=str(exc),
            ) from exc

        if response.status_code == 401:
            raise SatelliteAuthenticationError(
                "Sentinel Hub authentication was rejected while retrieving imagery.",
                details=response.text[:500],
            )

        if response.status_code == 403:
            raise SatelliteQuotaError(
                "Sentinel Hub quota or processing-unit limit has been reached. "
                "Please check your Sentinel Hub account quota or try again later.",
                details=response.text[:500],
            )

        if response.status_code >= 500:
            raise SatelliteServiceError(
                f"Sentinel Hub is temporarily unavailable "
                f"(status {response.status_code}). Please try again later.",
                details=response.text[:500],
            )

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
        content_type = response.headers.get("Content-Type", "")

        if not content_type.startswith("multipart"):
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

    def _build_process_request_body(self, request: SatelliteImageRequest, best_scene: CatalogScene) -> Dict[str, Any]:
        bounding_box = request.bounding_box()
        
        scene_date = best_scene.acquisition_date
        time_from = scene_date - timedelta(days=1)
        time_to = scene_date + timedelta(days=1)

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
                            }
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