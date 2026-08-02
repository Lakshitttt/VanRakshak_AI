"""
Image preprocessing pipeline for the AI engine.

Recreates, exactly, the preprocessing pipeline used during training of
the ResNet50 model: resize to 224x224, convert to tensor, and normalize
using ImageNet mean/std statistics. Any deviation from these exact values
would cause the model to receive out-of-distribution inputs.
"""

from typing import Final, List

from torchvision import transforms

# --- Fixed preprocessing parameters (must match training exactly) ---
IMAGE_SIZE: Final[int] = 224
NORMALIZE_MEAN: Final[List[float]] = [0.485, 0.456, 0.406]
NORMALIZE_STD: Final[List[float]] = [0.229, 0.224, 0.225]


def get_inference_transform() -> transforms.Compose:
    """
    Build the image transform pipeline used at inference time.

    Returns:
        A torchvision `Compose` transform that resizes an input PIL
        image to 224x224, converts it to a tensor, and normalizes it
        using the same mean/std statistics used during training.
    """
    return transforms.Compose(
        [
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=NORMALIZE_MEAN, std=NORMALIZE_STD),
        ]
    )