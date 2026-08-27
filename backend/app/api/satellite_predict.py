"""
FastAPI Router for Satellite-Based Land Cover Prediction.

This endpoint bridges the Sentinel Hub downloader and the ResNet50 ML model. 
It synchronously downloads the best available scene for the requested coordinates, 
runs in-memory inference, and returns a combined metadata/prediction report.
"""

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# backend/app/api -> backend/app -> backend -> project root
PROJECT_ROOT = os.path.abspath(
    os.path.join(CURRENT_DIR, "../../..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import APIRouter, HTTPException
from app.services.satellite.exceptions import (
    SatelliteError,
    SatelliteAuthenticationError,
    SatelliteQuotaError,
    SatelliteNetworkError,
    SatelliteServiceError,
    NoSatelliteImageryAvailableError,
)

# Schemas
from app.schemas.location import LocationRequest
from app.schemas.prediction import SatellitePredictionResponse

# Satellite Subsystem
from app.services.satellite.models import SatelliteImageRequest
from app.services.satellite.downloader import download_satellite_image

# ML Subsystem
from ml.src.predictor import predict_image

router = APIRouter()

@router.post("/", response_model=SatellitePredictionResponse)
def predict_from_satellite(request_data: LocationRequest):
    """
    End-to-end satellite prediction endpoint:
    1. Converts LocationRequest to SatelliteImageRequest.
    2. Synchronously downloads the best Sentinel-2 image.
    3. Runs ResNet50 inference natively on the downloaded PNG.
    4. Returns the combined satellite metadata and ML prediction report.
    """
    try:
        # 1. Map incoming LocationRequest to the internal SatelliteImageRequest
        # (Passes latitude and longitude. Add buffer/dimensions here if LocationRequest supports them)
        sat_request = SatelliteImageRequest(
            latitude=request_data.latitude,
            longitude=request_data.longitude
        )

        # 2. Trigger the synchronous satellite download pipeline
        satellite_result = download_satellite_image(sat_request)
        
        if not satellite_result or not satellite_result.image_path or not os.path.exists(satellite_result.image_path):
            raise HTTPException(
                status_code=500, 
                detail="Satellite pipeline succeeded, but the image file was not found on disk."
            )

        # 3. Run ML Inference 
        # Passes the absolute path of the downloaded PNG directly to the loaded ResNet50 model
        ml_results = predict_image(satellite_result.image_path)

        # 4. Construct and return the merged JSON response
        return SatellitePredictionResponse(
            prediction=ml_results["prediction"],
            confidence=ml_results["confidence"],
            confidence_level=ml_results["confidence_level"],
            top3=ml_results["top3"],
            prediction_time=ml_results["prediction_time"],
            acquisition_date=satellite_result.acquisition_date,
            provider=satellite_result.provider,
            latitude=satellite_result.latitude,
            longitude=satellite_result.longitude
        )

    except HTTPException:
        # Re-raise standard FastAPI HTTP exceptions unchanged.
        raise

    except SatelliteAuthenticationError as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "SATELLITE_AUTHENTICATION_ERROR",
                "message": str(e),
            },
        ) from e

    except SatelliteQuotaError as e:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "SATELLITE_QUOTA_ERROR",
                "message": str(e),
            },
        ) from e

    except SatelliteNetworkError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SATELLITE_NETWORK_ERROR",
                "message": str(e),
            },
        ) from e

    except SatelliteServiceError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SATELLITE_SERVICE_ERROR",
                "message": str(e),
            },
        ) from e

    except NoSatelliteImageryAvailableError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "NO_SATELLITE_IMAGERY",
                "message": str(e),
            },
        ) from e

    except SatelliteError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SATELLITE_ERROR",
                "message": str(e),
            },
        ) from e

    except Exception as e:
        import traceback

        print("\n" + "=" * 60)
        print("SATELLITE PIPELINE ERROR")
        print("Exception Type :", type(e).__name__)
        print("Exception      :", str(e))
        print("-" * 60)
        traceback.print_exc()
        print("=" * 60 + "\n")

        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred in the satellite prediction pipeline.",
            },
        ) from e