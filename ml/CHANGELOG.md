# 📜 VanRakshak AI Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog.

---

# [v0.5] - 2026-08-03

## Added

- FastAPI backend architecture.
- Prediction API (`POST /api/v1/predict`).
- Health API (`GET /api/v1/health`).
- Interactive Leaflet map.
- Location Selection API (`POST /api/v1/location/select`).
- Upload page with drag-and-drop support.
- Prediction result card.
- Frontend ↔ Backend communication.
- Production ResNet50 model integration.
- PROJECT_CONTEXT.md documentation.

## Changed

- Standardized backend architecture.
- Adopted service-based validation for coordinates.
- Added dedicated production model (`best_resnet50.pth`).

## Fixed

- Python virtual environment conflicts.
- Missing FastAPI dependency.
- Missing `pydantic-settings`.
- Missing `python-multipart`.
- CORS configuration.
- Upload result rendering.
- Homepage navigation.
- Git tracking for production model.

---

# Upcoming (v0.6)

Planned

- Sentinel-2 compatibility validation.
- Satellite provider abstraction.
- Satellite image retrieval.
- Map → AI inference pipeline.