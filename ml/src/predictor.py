"""
VanRakshak AI - ML Inference Module
Exposes a clean `predict_image` API designed for integration with FastAPI.
Loads the model globally so it stays in memory across multiple API requests.
"""

import os
import time
from typing import Dict, Any

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from ml.src.model import create_model
from ml.src.data import classes
# -----------------------------
# Path Resolution & Device
# -----------------------------
# Robust path resolution ensures the model loads correctly even when imported from the FastAPI backend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "best_resnet50.pth")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[Predictor] Initializing on device: {device}")

# -----------------------------
# Global Model Initialization
# -----------------------------
# Loaded once at module import to prevent high latency during individual API calls
model = create_model().to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()
print("[Predictor] ✅ ResNet50 model loaded successfully in memory.")

# -----------------------------
# Transformations
# -----------------------------
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# -----------------------------
# Inference Functions
# -----------------------------
def get_confidence_level(confidence_pct: float) -> str:
    """Categorizes confidence into qualitative levels."""
    if confidence_pct >= 90.0:
        return "Excellent"
    elif confidence_pct >= 75.0:
        return "High"
    elif confidence_pct >= 50.0:
        return "Moderate"
    return "Low"

def predict_image(image_path: str) -> Dict[str, Any]:
    """
    Runs inference on a single image and returns a JSON-serializable dictionary.
    
    Args:
        image_path (str): The absolute or relative path to the image file.
        
    Returns:
        dict: Contains prediction, confidence, confidence_level, top3 predictions, and execution time.
    """
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        raise ValueError(f"Failed to open image at {image_path}: {e}")

    # Preprocess
    image_tensor = transform(image)
    image_tensor = image_tensor.unsqueeze(0).to(device)

    # Inference with timing
    start_time = time.perf_counter()
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = F.softmax(outputs, dim=1)
        top_probs, top_indices = torch.topk(probabilities, 3)
    end_time = time.perf_counter()

    exec_time = end_time - start_time

    # Process results
    predicted_class = classes[top_indices[0][0].item()]
    confidence = top_probs[0][0].item() * 100

    top3_list = []
    for i in range(3):
        cls_name = classes[top_indices[0][i].item()]
        prob = top_probs[0][i].item() * 100
        top3_list.append({"class": cls_name, "confidence": prob})

    return {
        "prediction": predicted_class,
        "confidence": confidence,
        "confidence_level": get_confidence_level(confidence),
        "top3": top3_list,
        "prediction_time": exec_time
    }