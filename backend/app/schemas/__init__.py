"""
Schemas package for the VanRakshak AI backend.

Contains Pydantic request/response models that define the API's data
contracts, keeping response shapes declared in exactly one place.
"""

from app.schemas.prediction import PredictionResponse

__all__ = ["PredictionResponse"]