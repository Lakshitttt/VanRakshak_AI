"""
Pydantic schemas for the prediction endpoint.

Defines the response contract for POST /api/v1/predict. This is the
single source of truth for the shape of a prediction response; no route
or service constructs the equivalent dictionary by hand.
"""

from pydantic import BaseModel, ConfigDict, Field


class PredictionResponse(BaseModel):
    """
    Response body for a successful image classification.

    Attributes:
        class_: The predicted land cover class label. Serialized as
            "class" in the JSON response — the Python identifier `class`
            is reserved, so the field is named `class_` with an alias.
        confidence: The model's confidence in the predicted class, as a
            percentage between 0.0 and 100.0.
    """

    model_config = ConfigDict(populate_by_name=True)

    class_: str = Field(alias="class", description="Predicted land cover class.")
    confidence: float = Field(description="Confidence percentage, 0.0 to 100.0.")