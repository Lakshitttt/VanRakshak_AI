# 🌍 VanRakshak AI

> Protecting Forests Through Artificial Intelligence

---

# PROJECT CONTEXT

**Version:** 1.0

**Last Updated:** 03 August 2026

**Project Status:** Development & Validation

**Repository:** VanRakshak_AI

---

# 1. Executive Summary

## Project Overview

VanRakshak AI is an Artificial Intelligence powered environmental monitoring platform developed to classify land-cover using satellite imagery.

The project combines:

- Deep Learning
- Computer Vision
- Geospatial Mapping
- Web Technologies

into a single application.

Instead of requiring users to understand GIS software or satellite imagery processing, the system aims to provide a simple interface where a user can upload an image or select a location on an interactive map and obtain an AI-generated land-cover prediction.

---

## Why this project exists

Environmental monitoring is becoming increasingly important due to rapid urbanization, deforestation, climate change, and changes in land use.

Satellite imagery is widely available, but interpreting it requires expertise.

Our objective is to make satellite image analysis significantly more accessible through Artificial Intelligence.

---

## Target Users

- Students
- Researchers
- NGOs
- Environmental organizations
- Government agencies
- GIS beginners
- Anyone interested in land-cover analysis

---

## Long-Term Vision

The long-term objective is to allow a user to:

Select any point on Earth

↓

Retrieve satellite imagery

↓

Analyze it using AI

↓

Compare multiple years

↓

Detect environmental changes

↓

Generate a simple report

---

# 2. Current Development Status

## Current Phase

The project is currently in the **Development & Validation** stage.

This is extremely important.

The project is **NOT complete**.

We are **NOT integrating everything yet.**

Instead, every module is developed and validated independently before becoming part of the complete system.

Current workflow:

```
Feature Development

↓

Local Testing

↓

Output Verification

↓

Bug Fixing

↓

Performance Validation

↓

Integration

↓

System Testing

↓

Deployment
```

The philosophy behind this approach is to reduce debugging complexity by ensuring each component works correctly before connecting it to the next.

---

## Overall Completion

Approximate progress:

| Module | Status |
|---------|--------|
| Backend Foundation | ✅ Complete |
| Upload Workflow | ✅ Complete |
| Prediction API | ✅ Complete |
| Interactive Map | ✅ Complete |
| Location Selection API | ✅ Complete |
| Frontend Upload Interface | ✅ Complete |
| AI Upload Prediction | ✅ Complete |
| Satellite Provider | 🚧 In Progress |
| Satellite Retrieval | ⏳ Planned |
| Historical Comparison | ⏳ Planned |
| PDF Report | ⏳ Planned |
| Deployment | ⏳ Planned |

Estimated overall completion:

~55%

---

# 3. Project Vision

VanRakshak AI is intended to evolve beyond a simple image classifier.

The final application should become a complete environmental intelligence platform.

The intended user workflow is:

```
User

↓

Interactive Map

↓

Select Location

↓

Satellite Imagery Retrieval

↓

Image Preprocessing

↓

AI Prediction

↓

Historical Comparison

↓

Environmental Report
```

The AI should never analyze browser map screenshots.

Instead, it should always analyze actual satellite imagery downloaded from a satellite imagery provider.

---

# 4. Current Features

## Backend

Implemented:

- FastAPI application
- Modular project architecture
- Centralized settings
- Logging system
- Exception handling
- Health endpoint
- Prediction endpoint
- Location Selection endpoint

---

### Health Endpoint

```
GET /api/v1/health
```

Purpose:

Verify that the backend is running correctly.

Returns:

- service status
- application name
- version

---

### Prediction Endpoint

```
POST /api/v1/predict
```

Purpose:

Accept a satellite image uploaded by the user and classify it using the production ResNet50 model.

Input:

Multipart image upload.

Output:

```json
{
    "class": "Forest",
    "confidence": 97.2
}
```

---

### Location Selection Endpoint

```
POST /api/v1/location/select
```

Purpose:

Accept coordinates selected on the interactive map.

Current functionality:

- Validate latitude
- Validate longitude
- Return confirmation

Current limitation:

Does NOT yet retrieve satellite imagery.

This endpoint exists to establish frontend-backend communication before integrating satellite providers.

---

## Frontend

Completed pages:

- Landing Page
- Upload Page
- Interactive Map

Implemented features:

- Responsive layout
- Drag & Drop upload
- Image preview
- Prediction result card
- Leaflet interactive map
- Marker placement
- Coordinate selection
- Frontend → Backend communication

---

# 5. Machine Learning Overview

Current production model:

```
best_resnet50.pth
```

Location:

```
ml/models/
```

Architecture:

ResNet50

Dataset:

EuroSAT

Approximate validation accuracy:

~96%

The upload workflow already uses this model successfully.

This model is considered the production model.

The remaining model files are retained for historical purposes but are NOT used by the application.

---

# 6. Current Validation Stage

At the moment we are validating whether every independent component produces the desired output before integrating the complete system.

Current validation tasks include:

✔ Upload inference

✔ Prediction accuracy

✔ Frontend-backend communication

✔ Coordinate validation

✔ Interactive map

Current active validation:

Sentinel-2 compatibility.

Objective:

Determine whether Sentinel-2 imagery downloaded through Sentinel Hub can be used directly with the existing ResNet50 model trained on EuroSAT.

This validation will be performed before integrating satellite imagery into the backend.

No retraining is currently planned.

---

# 7. Development Philosophy

Several architectural decisions guide this project.

## Thin API Routes

API routes should contain almost no business logic.

Responsibilities:

Receive request

↓

Validate

↓

Call service

↓

Return response

Business logic belongs inside service modules.

---

## Single Responsibility Principle

Each module should perform one task only.

Example:

```
validator.py
```

Only validates coordinates.

It should never:

- return HTTP responses
- perform AI inference
- access databases
- retrieve satellite imagery

---

## Incremental Development

Every feature follows the same lifecycle:

```
Design

↓

Implementation

↓

Testing

↓

Validation

↓

Commit

↓

Integration
```

Only validated features become part of the main application.

---

## Stable Production Model

Current production model:

```
best_resnet50.pth
```

This model must not be replaced unless another model demonstrates measurable improvement through validation.

---

# 8. Immediate Next Goal

The next development milestone is the integration of a satellite imagery provider.

The expected future pipeline is:

```
Map

↓

Coordinates

↓

Satellite Provider

↓

Sentinel-2 Image

↓

Preprocessing

↓

ResNet50

↓

Prediction

↓

Result
```

Before integration, Sentinel-2 imagery will be validated independently to ensure compatibility with the existing model.
---

# 9. Repository Structure

The project follows a modular architecture where the Machine Learning model, backend, and frontend are separated into independent components.

```
VanRakshak_AI/

│
├── backend/
│
├── frontend/
│
├── ml/
│
├── PROJECT_CONTEXT.md
│
├── README.md
│
└── requirements.txt
```

Each directory has a specific responsibility.

---

# backend/

Purpose

Contains the complete FastAPI application responsible for serving APIs, handling requests, running AI inference, validating inputs, and communicating with the frontend.

The backend intentionally contains almost no frontend logic.

Major folders include:

```
backend/

app/

api/

core/

schemas/

services/

models/

utils/
```

---

## backend/app/api

Purpose

Contains API route definitions.

These files should only:

- Receive requests
- Validate request format
- Call service layer
- Return responses

Business logic must never live here.

Current APIs

health.py

Provides

```
GET /api/v1/health
```

predict.py

Provides

```
POST /api/v1/predict
```

location.py

Provides

```
POST /api/v1/location/select
```

---

## backend/app/core

Purpose

Contains shared backend infrastructure.

Includes

- application settings
- logging
- constants
- exception classes

Everything used globally belongs here.

---

## backend/app/services

Purpose

Contains business logic.

Current services

```
location/

validator.py
```

This validates latitude and longitude.

Future services

```
satellite/

imagery/

reports/

comparison/
```

will also live here.

---

## backend/app/schemas

Purpose

Defines API request and response schemas using Pydantic.

These files describe

Input

↓

Validation of structure

↓

Output

They intentionally avoid business logic.

---

# frontend/

Purpose

Contains the complete website.

Current pages

```
index.html

upload.html

map.html
```

Current JavaScript

```
upload.js

map.js

ui.js
```

Current styles

```
variables.css

base.css

components.css

animations.css
```

The frontend communicates with the backend exclusively through REST APIs.

It never performs AI inference directly.

---

# ml/

Purpose

Contains everything related to Machine Learning.

Current structure

```
ml/

models/

training/

datasets/

notebooks/
```

(Current structure may evolve.)

---

## Production Model

```
ml/models/best_resnet50.pth
```

This is the ONLY production model currently used.

Other checkpoints remain for historical purposes.

Do not replace the production model without validation.

---

# 10. Technology Stack

The project intentionally uses widely adopted technologies so that deployment and future maintenance remain straightforward.

---

## Programming Language

Python

Purpose

Backend

Machine Learning

Training

Inference

Utilities

---

## Backend Framework

FastAPI

Reason

- High performance
- Automatic API documentation
- Built-in validation
- Excellent async support
- Easy deployment

---

## Frontend

HTML

CSS

JavaScript

Reason

Simple

Lightweight

Easy deployment

No unnecessary framework overhead for the MVP.

---

## Machine Learning

PyTorch

Reason

Industry-standard deep learning framework.

Provides

- GPU support
- Transfer learning
- Easy deployment
- Mature ecosystem

---

## Model

ResNet50

Reason

Excellent balance between

Accuracy

Speed

Transfer learning capability

Widely validated architecture.

---

## Dataset

EuroSAT

Reason

Well-established benchmark for satellite image classification.

Contains multiple land-cover categories directly aligned with project goals.

---

## Interactive Map

Leaflet.js

Reason

Open source

Lightweight

Easy integration

Large plugin ecosystem

---

## Mapping Provider

OpenStreetMap

Current use

User interaction only.

The AI never analyzes OpenStreetMap tiles.

---

## Satellite Imagery

Current Status

Under evaluation.

Current preferred provider

Sentinel Hub

Reason

Provides Sentinel-2 imagery.

The compatibility with the trained model is currently under validation.

---

## Version Control

Git

GitHub

Used for

Version control

Collaboration

Code review

Project history

---

# 11. Machine Learning Pipeline

Current production pipeline

```
User Upload

↓

Image Validation

↓

RGB Conversion

↓

Resize

↓

Tensor Conversion

↓

Normalization

↓

ResNet50

↓

Prediction

↓

Confidence

↓

Frontend
```

---

## Planned Pipeline

```
Interactive Map

↓

Coordinates

↓

Satellite Provider

↓

Sentinel-2 Image

↓

Existing Preprocessing

↓

ResNet50

↓

Prediction

↓

Result Card
```

The objective is to reuse exactly the same inference pipeline currently used by the upload workflow.

No duplicate inference pipelines should exist.

---

# 12. Model Documentation

Architecture

ResNet50

Dataset

EuroSAT

Framework

PyTorch

Purpose

Land-cover classification.

Production File

```
best_resnet50.pth
```

Current Status

Production model.

Approximate Accuracy

~96%

Current Labels

AnnualCrop

Forest

HerbaceousVegetation

Highway

Industrial

Pasture

PermanentCrop

Residential

River

SeaLake

Future retraining should only occur if measurable improvements justify replacing the production model.

---

# 13. API Documentation

Health Endpoint

```
GET /api/v1/health
```

Purpose

Verify backend availability.

---

Prediction Endpoint

```
POST /api/v1/predict
```

Purpose

Predict land-cover from uploaded satellite imagery.

Input

Multipart image.

Output

Predicted class.

Confidence score.

---

Location Endpoint

```
POST /api/v1/location/select
```

Purpose

Receive validated coordinates from the frontend.

Current Responsibility

Coordinate validation only.

Future Responsibility

Trigger satellite imagery retrieval.
---

# 14. System Architecture

VanRakshak AI follows a layered architecture.

Each layer has a single responsibility.

```
                    USER
                      │
                      ▼
               Frontend Website
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
 Upload Workflow             Interactive Map
        │                           │
        └─────────────┬─────────────┘
                      │
                      ▼
               FastAPI Backend
                      │
      ┌───────────────┼────────────────┐
      │               │                │
      ▼               ▼                ▼
 Prediction API   Location API    Health API
      │               │
      ▼               ▼
 Business Services  Coordinate Validation
      │
      ▼
 Machine Learning Model
      │
      ▼
 Prediction Response
      │
      ▼
 Frontend Result Card
```

The architecture deliberately separates:

- User Interface
- API Layer
- Business Logic
- Machine Learning
- Future Satellite Services

This separation reduces coupling and simplifies testing.

---

# 15. Request Flow

## Upload Workflow

Current production workflow.

```
User

↓

Select Image

↓

upload.js

↓

POST /api/v1/predict

↓

FastAPI

↓

Image Validation

↓

Preprocessing

↓

ResNet50

↓

Prediction

↓

JSON Response

↓

Prediction Card
```

---

## Map Workflow

Current implementation.

```
User

↓

Leaflet Map

↓

Click Location

↓

Coordinates

↓

POST /api/v1/location/select

↓

Coordinate Validation

↓

Success Response
```

Future implementation.

```
User

↓

Leaflet Map

↓

Coordinates

↓

Satellite Provider

↓

Sentinel-2 Image

↓

Existing Preprocessing

↓

ResNet50

↓

Prediction

↓

Result
```

---

# 16. Major Engineering Decisions

Throughout development several important technical decisions were made.

---

## Decision 1

FastAPI instead of Flask.

Reason

FastAPI provides:

- automatic Swagger documentation
- request validation
- modern async support
- cleaner architecture

Decision Status

Accepted.

---

## Decision 2

Separate frontend and backend.

Reason

Allows

- easier deployment
- reusable APIs
- cleaner architecture
- independent development

Decision Status

Accepted.

---

## Decision 3

ResNet50

Reason

Excellent transfer learning performance.

Balanced speed and accuracy.

Already well validated on EuroSAT.

Decision Status

Accepted.

---

## Decision 4

Validate modules independently.

Instead of integrating everything immediately.

Reason

Large integrations create difficult debugging sessions.

Every feature must first pass local validation.

Decision Status

Accepted.

---

## Decision 5

Thin API Routes

API files should never contain business logic.

Responsibilities

Receive Request

↓

Validate

↓

Call Service

↓

Return Response

Decision Status

Accepted.

---

## Decision 6

Single Production Model

Only one production model exists.

```
best_resnet50.pth
```

Every inference uses this model.

Decision Status

Accepted.

---

## Decision 7

Interactive map does NOT perform inference.

Reason

The browser map is for user interaction only.

Actual inference must always use downloaded satellite imagery.

Decision Status

Accepted.

---

# 17. Development Timeline

## Phase 1

Project Planning

Completed

Activities

- project idea
- architecture planning
- technology selection

---

## Phase 2

Machine Learning

Completed

Activities

- dataset selection
- model training
- ResNet50 fine-tuning
- production model selection

---

## Phase 3

Backend

Completed

Activities

- FastAPI
- prediction endpoint
- health endpoint
- logging
- configuration

---

## Phase 4

Frontend

Completed

Activities

Landing Page

Upload Page

Interactive Map

Prediction Card

Image Preview

Leaflet Integration

---

## Phase 5

Frontend ↔ Backend Integration

Completed

Activities

Prediction API

Location API

Testing

Bug fixing

---

## Phase 6

Current Phase

Sentinel-2 compatibility validation.

Status

In Progress.

---

## Phase 7

Future

Satellite imagery retrieval.

Status

Pending.

---

## Phase 8

Future

Map → AI integration.

Status

Pending.

---

## Phase 9

Future

Historical comparison.

Status

Pending.

---

## Phase 10

Deployment

Status

Pending.

---

# 18. Bugs Encountered During Development

The following issues were encountered and resolved.

---

## Python Version Conflict

Issue

Multiple Python installations existed.

Symptoms

Incorrect packages imported.

Resolution

Standardized development using the project virtual environment.

Status

Resolved.

---

## Virtual Environment Confusion

Issue

VS Code occasionally used a different interpreter.

Resolution

Explicit activation of the correct virtual environment before running the backend.

Status

Resolved.

---

## Missing FastAPI

Issue

Backend failed during startup.

Cause

FastAPI not installed in active environment.

Resolution

Installed dependencies into the correct virtual environment.

Status

Resolved.

---

## Missing pydantic-settings

Issue

ModuleNotFoundError.

Resolution

Installed pydantic-settings.

Status

Resolved.

---

## Missing python-multipart

Issue

Upload endpoint crashed.

Resolution

Installed python-multipart.

Status

Resolved.

---

## CORS Errors

Issue

Frontend could not communicate with backend.

Resolution

Configured CORSMiddleware with frontend origin.

Status

Resolved.

---

## Upload Result Card

Issue

Prediction succeeded but frontend displayed nothing.

Resolution

JavaScript rendering updated.

Status

Resolved.

---

## Homepage Navigation

Issue

Landing page button did not open upload page.

Resolution

Updated links.

Status

Resolved.

---

## Git Ignore

Issue

Production model ignored.

Cause

```
*.pth
```

Resolution

Whitelisted

```
best_resnet50.pth
```

Status

Resolved.

---

# 19. Development Rules

Every contributor should follow these rules.

1.

One feature per commit.

---

2.

Test locally before pushing.

---

3.

Never bypass validation.

---

4.

Business logic belongs in services.

---

5.

Do not duplicate preprocessing.

---

6.

Never replace the production model without validation.

---

7.

Document major architectural decisions.

---

8.

Keep APIs backward compatible whenever possible.

---

9.

Prefer modular code over shortcuts.

---

10.

Every completed sprint should update:

- PROJECT_CONTEXT.md
- ROADMAP.md
- CHANGELOG.md
---

# 20. Team Responsibilities

The project consists of five members.

Responsibilities should remain clearly separated to avoid duplicate work and merge conflicts.

---

## Member 1 – Project Lead (Laksh)

Responsibilities

- Overall architecture
- Backend development
- Frontend development
- Machine Learning integration
- GitHub repository management
- Code review
- Final integration
- Deployment

Completed

- Project architecture
- FastAPI backend
- Upload workflow
- Interactive map
- Prediction API
- Location Selection API
- Frontend integration

Current Work

- Satellite service architecture
- Final integration
- Deployment preparation

---

## Member 2 – Satellite Validation

Responsibilities

- Sentinel Hub setup
- Sentinel-2 imagery retrieval
- Compatibility validation
- Test image collection

Current Objective

Determine whether Sentinel-2 imagery is compatible with the current production ResNet50 model.

Deliverables

- Validation script
- Test dataset
- Compatibility report
- Recommendations

---

## Member 3 – Testing & Quality Assurance

Responsibilities

- API testing
- Frontend testing
- Edge case testing
- Regression testing

Deliverables

- Bug reports
- Test cases
- Validation logs

---

## Member 4 – Documentation

Responsibilities

- Update README
- Maintain PROJECT_CONTEXT.md
- Maintain CHANGELOG
- Maintain ROADMAP
- API documentation

---

## Member 5 – Deployment & Demonstration

Responsibilities

- Deployment research
- Demo preparation
- Presentation support
- Performance testing

---

# 21. Current Validation Objectives

The project is currently validating individual modules before system integration.

Current validation objectives:

✔ Upload workflow

✔ AI inference

✔ Prediction accuracy

✔ Frontend ↔ Backend communication

✔ Coordinate validation

✔ Interactive map

Current active validation:

Sentinel-2 compatibility.

Questions being answered:

- Can Sentinel-2 imagery be used directly?

- Does the current preprocessing remain valid?

- Is retraining necessary?

- Does the model generalize well?

Only after these questions are answered will Sentinel Hub become part of the production pipeline.

---

# 22. Remaining Development Roadmap

## Sprint 1

Backend Foundation

Status

Completed

---

## Sprint 2

Upload Workflow

Status

Completed

---

## Sprint 3

Interactive Map

Status

Completed

---

## Sprint 4

Location Selection API

Status

Completed

---

## Sprint 5

Sentinel-2 Validation

Status

In Progress

Deliverables

- Sentinel Hub account
- Compatibility testing
- Validation report

---

## Sprint 6

Satellite Retrieval Service

Status

Pending

Deliverables

- Satellite abstraction layer
- Imagery retrieval
- Download pipeline

---

## Sprint 7

Map → AI Integration

Status

Pending

Deliverables

Map

↓

Coordinates

↓

Satellite Image

↓

ResNet50

↓

Prediction

---

## Sprint 8

Historical Comparison

Status

Pending

Deliverables

- Compare years
- Vegetation changes
- Difference visualization

---

## Sprint 9

Report Generation

Status

Pending

Deliverables

- PDF export
- Summary
- Prediction confidence

---

## Sprint 10

Deployment

Status

Pending

Deliverables

- Production deployment
- Final testing
- Demo

---

# 23. Current TODO List

## Critical

- [ ] Validate Sentinel-2 compatibility.
- [ ] Build satellite provider abstraction.
- [ ] Retrieve Sentinel-2 imagery.
- [ ] Connect map workflow to AI.
- [ ] End-to-end testing.

---

## High Priority

- [ ] Historical comparison.
- [ ] Report generation.
- [ ] Deployment configuration.

---

## Medium Priority

- [ ] Improve documentation.
- [ ] API refinement.
- [ ] Performance optimization.

---

## Low Priority

- [ ] UI polish.
- [ ] Additional animations.
- [ ] Theme customization.

These items intentionally remain low priority until core functionality is complete.

---

# 24. Known Risks

## Model Domain Shift

Risk

Sentinel-2 imagery may differ from EuroSAT samples.

Mitigation

Compatibility testing before integration.

---

## Integration Bugs

Risk

Independent modules may fail after integration.

Mitigation

Incremental integration.

---

## API Changes

Risk

Breaking frontend communication.

Mitigation

Maintain backward compatibility.

---

## Model Replacement

Risk

Replacing production model without validation.

Mitigation

Always compare against current production model.

---

## Deployment Differences

Risk

Production environment differs from local environment.

Mitigation

Document dependencies.

Test before deployment.

---

# 25. Important Rules

Never:

- Modify production preprocessing.
- Replace best_resnet50.pth without evidence.
- Skip validation.
- Mix frontend logic into backend.
- Place business logic inside API routes.
- Commit multiple unrelated features together.

Always:

- Test locally.
- Keep commits small.
- Update documentation.
- Push working code.
- Validate before merge.

---

# 26. Immediate Next Steps

Current priority order:

1.

Finish Sentinel-2 compatibility validation.

↓

2.

Implement satellite retrieval service.

↓

3.

Connect map coordinates to retrieved imagery.

↓

4.

Run AI inference.

↓

5.

Display prediction.

↓

6.

Historical comparison.

↓

7.

Deployment.

This order should not be changed without team discussion.

---

# 27. Quick Start For New Developers

Clone repository.

↓

Create virtual environment.

↓

Install dependencies.

↓

Run backend.

↓

Run frontend.

↓

Open upload page.

↓

Verify AI prediction.

↓

Open map.

↓

Verify coordinate selection.

↓

Read PROJECT_CONTEXT.md.

↓

Choose assigned task.

---

# 28. Final Notes

PROJECT_CONTEXT.md is the official technical reference for VanRakshak AI.

When major architectural decisions are made, this document must be updated before beginning the next sprint.

The objective is that any new developer—or any future AI session—can understand the project without needing previous conversations.

This document should evolve together with the project and always reflect the current implementation.