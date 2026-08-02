"""
Class label definitions for the AI engine.

Contains only the EuroSAT RGB class labels the trained ResNet50 model
predicts, in the exact order matching the model's output layer. No
inference logic lives in this file.
"""

from typing import Final, List

from app.core.constants import EUROSAT_CLASSES

# Re-exported here (not redefined) so every ai_engine module has a single,
# local import point for labels without duplicating the class list that
# already exists as project data in app/core/constants.py.
CLASS_LABELS: Final[List[str]] = EUROSAT_CLASSES