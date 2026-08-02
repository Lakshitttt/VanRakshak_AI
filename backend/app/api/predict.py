"""
Prediction endpoint.

Accepts an uploaded satellite image, validates and decodes it, and
delegates to the AI engine's `predict` function for inference. This
module contains no inference logic itself — it only orchestrates the
request/response cycle around the already-implemented AI engine.
"""

import io
from typing import Final

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.ai_engine import predict as run_prediction
from app.schemas.prediction import PredictionResponse

router: Final[APIRouter] = APIRouter(tags=["Prediction"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Classify a satellite image",
)
async def predict_image(
    image: UploadFile = File(..., description="Satellite image to classify"),
) -> PredictionResponse:
    """
    Classify an uploaded satellite image using the trained AI engine.

    Reads the uploaded file, decodes it as an image, converts it to RGB
    if necessary, and passes it to the AI engine's `predict` function.

    Args:
        image: The uploaded image file, provided as multipart/form-data
            under the field name `image`.

    Returns:
        A PredictionResponse containing the predicted land cover class
        and confidence percentage.

    Raises:
        HTTPException: 400 if the uploaded file is empty, not a valid
            image, corrupted, or in an unsupported format.
    """
    file_bytes = await image.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        pil_image = Image.open(io.BytesIO(file_bytes))
        pil_image.load()
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid or supported image.",
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image is corrupted and could not be read.",
        ) from exc

    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    result = run_prediction(pil_image)

    return PredictionResponse(class_=result["class"], confidence=result["confidence"])