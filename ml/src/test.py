import torch
from sklearn.metrics import classification_report, confusion_matrix
from model import create_model
from data import test_loader, classes

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Using:", device)

model = create_model().to(device)
model.load_state_dict(torch.load("models/best_resnet50.pth", map_location=device))
model.eval()

correct = 0
total = 0

all_labels = []
all_predictions = []

with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)

        _, predicted = torch.max(outputs, 1)

        total += labels.size(0)
        correct += (predicted == labels).sum().item()

        all_labels.extend(labels.cpu().numpy())
        all_predictions.extend(predicted.cpu().numpy())

accuracy = 100 * correct / total

print(f"\nTest Accuracy: {accuracy:.2f}%\n")

print(classification_report(
    all_labels,
    all_predictions,
    target_names=classes
))

cm = confusion_matrix(all_labels, all_predictions)

print("Confusion Matrix:\n")
print(cm)