"""
Prediction orchestration service for the AI engine.

Provides a single pure-Python function that takes an already-opened PIL
image and returns the predicted class and confidence, by coordinating
the transform pipeline, the singleton model, and the classifier. This
module has no knowledge of FastAPI, HTTP, or file uploads — it accepts
a PIL.Image.Image and nothing else.
"""

from typing import Dict, Union

from PIL.Image import Image

from app.ai_engine.classifier import classify
from app.ai_engine.model_loader import get_device, get_model
from app.ai_engine.transforms import get_inference_transform


def predict(image: Image) -> Dict[str, Union[str, float]]:
    """
    Predict the land cover class of a single satellite image.

    Args:
        image: An already-opened PIL image (e.g. `PIL.Image.open(...)`).
            This function does not open, fetch, or validate files itself.

    Returns:
        A dictionary with the shape:
            {
                "class": <predicted class label as str>,
                "confidence": <confidence percentage as float>,
            }
    """
    model = get_model()
    device = get_device()
    transform = get_inference_transform()

    image_tensor = transform(image)
    predicted_class, confidence = classify(model, device, image_tensor)

    return {
        "class": predicted_class,
        "confidence": confidence,
    }