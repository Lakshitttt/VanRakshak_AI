"""
Application-wide constants for the VanRakshak AI backend.

Values here are fixed facts about the project (identity, known model
output classes, API versioning prefix) rather than environment-specific
configuration, which belongs in app/core/settings.py instead.
"""

from typing import Final, List

# --- Application identity ---
# Mirrors the defaults in app/core/settings.py for use in contexts where
# importing Settings is undesirable (e.g. plain constant string literals).
APP_NAME: Final[str] = "VanRakshak AI"
APP_TAGLINE: Final[str] = "Protecting Forests Through Artificial Intelligence"

# --- API versioning ---
API_V1_PREFIX: Final[str] = "/api/v1"

# --- EuroSAT RGB class labels ---
# Order matches the trained ResNet50 model's output layer
# (models/best_resnet50.pth). This is fixed project data describing the
# already-completed model; it does not activate any prediction behavior
# on its own and is not used anywhere in this foundation task.
EUROSAT_CLASSES: Final[List[str]] = [
    "AnnualCrop",
    "Forest",
    "HerbaceousVegetation",
    "Highway",
    "Industrial",
    "Pasture",
    "PermanentCrop",
    "Residential",
    "River",
    "SeaLake",
]