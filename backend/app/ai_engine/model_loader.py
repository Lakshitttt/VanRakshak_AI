"""
Model loading for the AI engine.

Responsible for constructing the ResNet50 architecture, loading the
already-trained weights from disk, placing the model on the correct
device, and putting it in evaluation mode. The loaded model is exposed
as a process-wide singleton so it is never reloaded per request.

No training code exists here or anywhere in this module — the model is
already trained; this file only performs inference-time loading.
"""

import threading
from pathlib import Path
from typing import Final, Optional

import torch
from torch import nn
from torchvision import models

from app.ai_engine.labels import CLASS_LABELS

# --- Fixed loading parameters ---
# Path is resolved relative to this file so it is correct regardless of
# the process's current working directory. Project layout:
#
# VanRakshak_AI/                                  <- project root
# ├── backend/
# │   └── app/ai_engine/model_loader.py            <- this file
# ├── frontend/
# └── ml/
#     ├── dataset/
#     └── models/best_resnet50.pth
#
# backend/app/ai_engine -> app -> backend -> VanRakshak_AI (project root),
# then into the sibling ml/models/ directory.
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent.parent
MODEL_PATH: Final[Path] = PROJECT_ROOT / "ml" / "models" / "best_resnet50.pth"

NUM_CLASSES: Final[int] = len(CLASS_LABELS)

# --- Classifier head parameters (must match training exactly) ---
CLASSIFIER_HIDDEN_UNITS: Final[int] = 512
CLASSIFIER_DROPOUT: Final[float] = 0.3

# --- Singleton state ---
_model: Optional[nn.Module] = None
_device: Optional[torch.device] = None
_lock: threading.Lock = threading.Lock()


def _build_architecture() -> nn.Module:
    """
    Construct the ResNet50 architecture matching the trained checkpoint.

    The final fully-connected layer is replaced with the exact classifier
    head used during training: a hidden Linear layer, ReLU activation,
    Dropout, and a final Linear layer projecting to `NUM_CLASSES` logits.
    No pretrained ImageNet weights are downloaded here; the architecture
    is only a shell that the trained checkpoint's weights are loaded into.

    Returns:
        An uninitialized ResNet50 `nn.Module` whose classifier head
        matches the training architecture, ready to receive trained
        weights.
    """
    architecture = models.resnet50(weights=None)
    in_features = architecture.fc.in_features

    architecture.fc = nn.Sequential(
        nn.Linear(in_features, CLASSIFIER_HIDDEN_UNITS),
        nn.ReLU(),
        nn.Dropout(CLASSIFIER_DROPOUT),
        nn.Linear(CLASSIFIER_HIDDEN_UNITS, NUM_CLASSES),
    )

    return architecture


def _resolve_device() -> torch.device:
    """
    Determine the device inference should run on.

    Returns:
        A CUDA device if one is available, otherwise the CPU device.
    """
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_model() -> nn.Module:
    """
    Return the singleton, trained ResNet50 model, loading it on first use.

    The model is constructed, has its trained weights loaded from
    `MODEL_PATH`, is moved to the resolved device, and is set to
    evaluation mode exactly once per process. Every subsequent call
    returns the same in-memory instance rather than reloading from disk.

    A lock guards the first load so concurrent callers during startup
    cannot trigger duplicate loads.

    Returns:
        The loaded, evaluation-mode ResNet50 model on its resolved device.
    """
    global _model, _device

    if _model is not None:
        return _model

    with _lock:
        if _model is not None:
            # Another thread completed the load while this one waited.
            return _model

        device = _resolve_device()
        model = _build_architecture()

        checkpoint = torch.load(MODEL_PATH, map_location=device)
        model.load_state_dict(checkpoint)

        model.to(device)
        model.eval()

        _device = device
        _model = model

    return _model


def get_device() -> torch.device:
    """
    Return the device the singleton model is loaded on.

    Ensures the model has been loaded (calling `get_model` if necessary)
    so the device is always defined and consistent with where the
    model's parameters actually live.

    Returns:
        The `torch.device` the singleton model is currently on.
    """
    if _device is None:
        get_model()
    return _device