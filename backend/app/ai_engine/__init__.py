"""
AI engine package for the VanRakshak AI backend.

Contains model loading, preprocessing, classification, and prediction
orchestration for the trained ResNet50 EuroSAT model. This is inference
only — no training code exists in this package.

Public entry point: `predict_service.predict`.
"""

from app.ai_engine.predict_service import predict

__all__ = ["predict"]