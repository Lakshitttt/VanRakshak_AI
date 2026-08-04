# 🛣️ VanRakshak AI Development Roadmap

> Living development roadmap for VanRakshak AI.

**Current Version:** v0.5

**Last Updated:** 03 August 2026

---

# Development Philosophy

VanRakshak AI follows an incremental development approach.

Every feature progresses through the following lifecycle:

```
Design

↓

Implementation

↓

Testing

↓

Validation

↓

Integration

↓

Deployment
```

No feature is integrated into the production workflow until it has been independently validated.

---

# Current Project Status

| Sprint | Status |
|---------|--------|
| Sprint 1 - Backend Foundation | ✅ Completed |
| Sprint 2 - AI Upload Workflow | ✅ Completed |
| Sprint 3 - Interactive Map | ✅ Completed |
| Sprint 4 - Location Selection API | ✅ Completed |
| Sprint 5 - Sentinel-2 Validation | 🚧 In Progress |
| Sprint 6 - Satellite Retrieval | ⏳ Pending |
| Sprint 7 - Map → AI Integration | ⏳ Pending |
| Sprint 8 - Historical Comparison | ⏳ Pending |
| Sprint 9 - Report Generation | ⏳ Pending |
| Sprint 10 - Deployment | ⏳ Pending |

---

# Sprint 1 — Backend Foundation

Status: ✅ Completed

Deliverables

- FastAPI backend
- Modular project structure
- Logging system
- Configuration management
- Health API
- Exception handling

---

# Sprint 2 — AI Upload Workflow

Status: ✅ Completed

Deliverables

- Upload page
- Drag & Drop
- Prediction API
- ResNet50 inference
- Prediction result card

---

# Sprint 3 — Interactive Map

Status: ✅ Completed

Deliverables

- Leaflet integration
- Search
- Marker placement
- Coordinate selection

---

# Sprint 4 — Location Selection API

Status: ✅ Completed

Deliverables

- POST /api/v1/location/select
- Coordinate validation
- Frontend-backend communication

---

# Sprint 5 — Sentinel-2 Compatibility Validation

Status: 🚧 In Progress

Objective

Validate whether Sentinel-2 imagery from Sentinel Hub is compatible with the current production ResNet50 model trained on EuroSAT.

Tasks

- Download Sentinel-2 imagery
- Apply existing preprocessing
- Run inference
- Compare predictions
- Document findings

Deliverables

- Validation script
- Compatibility report
- Recommendation

---

# Sprint 6 — Satellite Retrieval Service

Status: ⏳ Pending

Objective

Retrieve satellite imagery using map-selected coordinates.

Deliverables

- Satellite provider abstraction
- Sentinel Hub integration
- Image download pipeline

---

# Sprint 7 — Map → AI Integration

Status: ⏳ Pending

Objective

Connect the interactive map directly to the AI model.

Pipeline

Coordinates

↓

Satellite Image

↓

Preprocessing

↓

ResNet50

↓

Prediction

↓

Frontend

---

# Sprint 8 — Historical Comparison

Status: ⏳ Pending

Objective

Compare satellite imagery from different years.

Expected Features

- Multi-year comparison
- Forest change detection
- Urban expansion monitoring

---

# Sprint 9 — Report Generation

Status: ⏳ Pending

Objective

Generate downloadable reports.

Expected Output

- Prediction
- Confidence
- Location
- Date
- Summary

---

# Sprint 10 — Deployment

Status: ⏳ Pending

Objective

Deploy the application for public use.

Expected Tasks

- Backend deployment
- Frontend deployment
- Production testing
- Performance optimization

---

# Current Priorities

Priority 1

Sentinel-2 compatibility validation.

Priority 2

Satellite imagery retrieval.

Priority 3

Map → AI integration.

Priority 4

Historical comparison.

Priority 5

Deployment.

---

# Long-Term Vision

Future versions of VanRakshak AI may include:

- Multi-provider satellite support
- Time-series analysis
- Forest health monitoring
- Environmental risk alerts
- Mobile application
- Cloud deployment