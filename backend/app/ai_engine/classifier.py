"""
Classification logic for the AI engine.

Runs a preprocessed image tensor through the loaded model and returns
the predicted class label together with its confidence percentage. This
module contains no image loading, preprocessing, or file-handling logic
— it only classifies tensors it is given.
"""

from typing import Final, Tuple

import torch
from torch import nn

from app.ai_engine.labels import CLASS_LABELS

PERCENTAGE_MULTIPLIER: Final[float] = 100.0


def classify(model: nn.Module, device: torch.device, image_tensor: torch.Tensor) -> Tuple[str, float]:
    """
    Run inference on a single preprocessed image tensor.

    Args:
        model: The loaded, evaluation-mode ResNet50 model.
        device: The device the model is loaded on; the input tensor is
            moved to this device before inference.
        image_tensor: A preprocessed image tensor of shape (3, H, W),
            as produced by the transform pipeline in transforms.py.

    Returns:
        A tuple of (predicted_class_label, confidence_percentage), where
        confidence_percentage is a float between 0.0 and 100.0.
    """
    batch = image_tensor.unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(batch)
        probabilities = torch.softmax(logits, dim=1)
        confidence_tensor, predicted_index_tensor = torch.max(probabilities, dim=1)

    predicted_index = int(predicted_index_tensor.item())
    confidence_percentage = float(confidence_tensor.item()) * PERCENTAGE_MULTIPLIER

    predicted_label = CLASS_LABELS[predicted_index]

    return predicted_label, confidence_percentage