# 🌍 VanRakshak AI

<p align="center">

**Protecting Forests Through Artificial Intelligence**

An AI-powered environmental monitoring platform that combines satellite imagery, deep learning, and interactive mapping to make land-cover analysis accessible.

</p>

---

## 📖 Overview

VanRakshak AI is a full-stack Artificial Intelligence platform designed to classify land-cover from satellite imagery.

The project combines:

- 🧠 Deep Learning (ResNet50)
- 🛰️ Satellite Imagery
- 🗺️ Interactive Maps
- ⚡ FastAPI Backend
- 🌐 Modern Web Interface

into a single application.

The long-term vision is to allow users to select any location on Earth, retrieve satellite imagery, analyze it using AI, compare historical changes, and generate environmental reports.

---

## ✨ Current Features

### 🤖 AI Image Classification

- Upload satellite images
- ResNet50 inference
- Confidence score
- Real-time prediction

---

### 🗺️ Interactive Map

- Leaflet.js integration
- Search locations
- Select coordinates
- Backend communication

---

### ⚙️ Backend APIs

- Health API
- Prediction API
- Location Selection API

---

### 🎨 Frontend

- Responsive design
- Upload interface
- Drag & Drop support
- Prediction cards
- Interactive map

---

## 🏗️ System Architecture

```text
                 User
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
 Upload Image          Interactive Map
        │                     │
        └──────────┬──────────┘
                   ▼
            FastAPI Backend
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
 Prediction API       Location API
        │
        ▼
   ResNet50 Model
        │
        ▼
 Prediction Result
```

---

## 🚀 Planned Workflow

```text
Select Location

↓

Retrieve Sentinel-2 Imagery

↓

Image Preprocessing

↓

ResNet50 Inference

↓

Land-Cover Prediction

↓

Historical Comparison

↓

Environmental Report
```

---

## 🧠 Machine Learning

### Production Model

- **Architecture:** ResNet50
- **Framework:** PyTorch
- **Dataset:** EuroSAT
- **Production Weights:** `ml/models/best_resnet50.pth`
- **Approximate Validation Accuracy:** ~96%

### Current Classes

- AnnualCrop
- Forest
- HerbaceousVegetation
- Highway
- Industrial
- Pasture
- PermanentCrop
- Residential
- River
- SeaLake

---

## 💻 Technology Stack

| Layer | Technology |
|--------|------------|
| Backend | FastAPI |
| Frontend | HTML, CSS, JavaScript |
| ML Framework | PyTorch |
| Model | ResNet50 |
| Dataset | EuroSAT |
| Mapping | Leaflet.js |
| Map Provider | OpenStreetMap |
| Version Control | Git & GitHub |

---

## 📂 Repository Structure

```text
VanRakshak_AI/

├── backend/
├── frontend/
├── ml/
│   └── models/
│       └── best_resnet50.pth
│
├── PROJECT_CONTEXT.md
├── ROADMAP.md
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

---

## 📡 API Endpoints

| Method | Endpoint | Purpose |
|----------|-----------------------------|--------------------------------|
| GET | `/api/v1/health` | Backend health check |
| POST | `/api/v1/predict` | Predict uploaded image |
| POST | `/api/v1/location/select` | Validate selected coordinates |

---

## 📊 Development Status

| Module | Status |
|---------|--------|
| Backend | ✅ Complete |
| Upload Workflow | ✅ Complete |
| Interactive Map | ✅ Complete |
| Prediction API | ✅ Complete |
| Location Selection API | ✅ Complete |
| Sentinel Validation | 🚧 In Progress |
| Satellite Retrieval | ⏳ Planned |
| Historical Comparison | ⏳ Planned |
| Deployment | ⏳ Planned |

---

## 🎯 Current Focus

The project is **currently in the validation phase**.

We are validating each module independently before final integration.

Current priority:

- Validate Sentinel-2 compatibility with the production ResNet50 model.
- Build satellite imagery retrieval.
- Connect the map workflow directly to AI inference.

---

## 🛣️ Roadmap

- ✅ Backend Foundation
- ✅ AI Upload Workflow
- ✅ Interactive Map
- ✅ Location Selection API
- 🚧 Sentinel-2 Compatibility Validation
- ⏳ Satellite Retrieval Service
- ⏳ Map → AI Integration
- ⏳ Historical Comparison
- ⏳ Report Generation
- ⏳ Deployment

---

## 📚 Documentation

The repository includes detailed technical documentation.

| Document | Description |
|-----------|-------------|
| `PROJECT_CONTEXT.md` | Complete engineering handbook |
| `ROADMAP.md` | Development roadmap |
| `CHANGELOG.md` | Project history |

---

## 👥 Team

This project is being developed collaboratively as part of a Machine Learning project.

Development follows a modular approach where every feature is independently validated before being integrated into the complete system.

---

## 🤝 Contributing

All contributors should:

- Create one feature per commit.
- Test locally before pushing.
- Keep API routes thin.
- Place business logic inside services.
- Update documentation after major architectural changes.
- Never replace the production model without validation.

---

## 📄 License

This project is developed for educational and research purposes.

---

<p align="center">

**VanRakshak AI**

*Protecting Forests Through Artificial Intelligence* 🌿

</p>