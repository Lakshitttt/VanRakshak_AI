import os
import json
from pathlib import Path

import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
import matplotlib.pyplot as plt
import numpy as np

from model import create_model
from data import test_loader, classes

# ============================================================
# Device
# ============================================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# ============================================================
# Load Model
# ============================================================

MODEL_PATH = "../models/best_resnet50.pth"
model = create_model().to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

print("Model loaded successfully!")

# ============================================================
# Results Directory
# ============================================================

RESULTS_DIR = Path("../results")
RESULTS_DIR.mkdir(exist_ok=True)

# ============================================================
# Evaluation
# ============================================================

all_labels = []
all_predictions = []

correct = 0
total = 0

criterion = nn.CrossEntropyLoss()
running_loss = 0

with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)

        loss = criterion(outputs, labels)
        running_loss += loss.item()

        _, predicted = torch.max(outputs, 1)

        total += labels.size(0)
        correct += (predicted == labels).sum().item()

        all_labels.extend(labels.cpu().numpy())
        all_predictions.extend(predicted.cpu().numpy())

# ============================================================
# Metrics
# ============================================================

accuracy = accuracy_score(all_labels, all_predictions)

precision, recall, f1, _ = precision_recall_fscore_support(
    all_labels,
    all_predictions,
    average="weighted",
)

avg_loss = running_loss / len(test_loader)

print("\n===================================")
print("MODEL EVALUATION")
print("===================================")

print(f"Test Loss      : {avg_loss:.4f}")
print(f"Accuracy       : {accuracy*100:.2f}%")
print(f"Precision      : {precision*100:.2f}%")
print(f"Recall         : {recall*100:.2f}%")
print(f"F1 Score       : {f1*100:.2f}%")

# ============================================================
# Classification Report
# ============================================================

report = classification_report(
    all_labels,
    all_predictions,
    target_names=classes,
)

print("\nClassification Report\n")
print(report)

with open(RESULTS_DIR / "classification_report.txt", "w") as f:
    f.write(report)

# ============================================================
# Confusion Matrix
# ============================================================

cm = confusion_matrix(all_labels, all_predictions)

plt.figure(figsize=(10, 8))
plt.imshow(cm)

plt.xticks(np.arange(len(classes)), classes, rotation=90)
plt.yticks(np.arange(len(classes)), classes)

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")

plt.colorbar()

plt.tight_layout()

plt.savefig(RESULTS_DIR / "confusion_matrix.png")

# ============================================================
# Save Metrics
# ============================================================

metrics = {
    "accuracy": float(accuracy),
    "precision": float(precision),
    "recall": float(recall),
    "f1_score": float(f1),
    "loss": float(avg_loss),
}

with open(RESULTS_DIR / "metrics.json", "w") as f:
    json.dump(metrics, f, indent=4)

print("\nResults saved to:")
print("results/classification_report.txt")
print("results/confusion_matrix.png")
print("results/metrics.json")

print("\nEvaluation Complete!")