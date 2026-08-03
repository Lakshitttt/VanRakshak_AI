"""
Standalone validation script for the satellite retrieval subsystem.

Not a pytest suite — a runnable script that exercises the existing
Downloader and SentinelProvider against a real location, end to end
(authenticate -> Process API -> save -> result), without touching any
other part of the application.

Requires SENTINEL_HUB_CLIENT_ID / SENTINEL_HUB_CLIENT_SECRET to be
configured (via .env or environment variables) — see
app/core/satellite_settings.py.

Run from the backend/ directory:
    python tests/test_satellite_download.py

Or from anywhere:
    python /path/to/backend/tests/test_satellite_download.py
"""
from app.core.satellite_settings import satellite_settings

print("CLIENT ID:", satellite_settings.SENTINEL_HUB_CLIENT_ID)
print("SECRET EXISTS:", satellite_settings.SENTINEL_HUB_CLIENT_SECRET is not None)
print("SECRET LENGTH:", len(satellite_settings.SENTINEL_HUB_CLIENT_SECRET or ""))

import sys
from pathlib import Path

# Make the `app` package importable when this script is run directly,
# regardless of the current working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.satellite.downloader import download_satellite_image  # noqa: E402
from app.services.satellite.exceptions import SatelliteError  # noqa: E402
from app.services.satellite.models import SatelliteImageRequest  # noqa: E402

# --- Fixed test location ---
TEST_LATITUDE = 23.0775
TEST_LONGITUDE = 77.3610


def get_image_dimensions(image_path: Path) -> str:
    """
    Read the saved image's pixel dimensions for display purposes.

    Args:
        image_path: Path to the saved satellite image.

    Returns:
        A "WIDTHxHEIGHT" string, or a short explanation if the
        dimensions could not be determined.
    """
    try:
        from PIL import Image
    except ImportError:
        return "unavailable (Pillow is not installed)"

    try:
        with Image.open(image_path) as image:
            return f"{image.width}x{image.height}"
    except Exception:
        return "unavailable (could not read the saved image)"


def main() -> None:
    """
    Download a single Sentinel-2 image for the fixed test location and
    print the result, or a readable error if anything fails.
    """
    request = SatelliteImageRequest(
        latitude=TEST_LATITUDE,
        longitude=TEST_LONGITUDE,
    )

    try:
        result = download_satellite_image(request)
    except SatelliteError as exc:
        print("FAILED")
        print(f"Error: {exc.message}")
        if exc.details:
            print(f"Details: {exc.details}")
        return
    except Exception as exc:  # deliberately broad: this is a standalone diagnostic script
        print("FAILED")
        print(f"Unexpected error: {type(exc).__name__}: {exc}")
        return

    print("SUCCESS")
    print(f"Image path: {result.image_path}")
    print(f"Image dimensions: {get_image_dimensions(result.image_path)}")
    print(f"Provider: {result.provider}")
    print(f"Acquisition date: {result.acquisition_date if result.acquisition_date else 'not available'}")


if __name__ == "__main__":
    main()