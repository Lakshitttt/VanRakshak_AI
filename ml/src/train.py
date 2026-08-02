import copy
import torch
import torch.nn as nn
import torch.optim as optim

from model import create_model
from data import train_loader, val_loader

# -----------------------------
# Device
# -----------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"\nUsing Device: {device}")

# -----------------------------
# Model
# -----------------------------
model = create_model().to(device)
print("ResNet50 loaded successfully!\n")

criterion = nn.CrossEntropyLoss()

optimizer = optim.Adam(
    model.fc.parameters(),
    lr=0.001
)

epochs = 5

train_loss_history = []
train_acc_history = []

val_loss_history = []
val_acc_history = []

best_val_accuracy = 0.0
best_model_weights = copy.deepcopy(model.state_dict())

# ===========================================================
# TRAINING
# ===========================================================

for epoch in range(epochs):

    print(f"\n========== Epoch {epoch+1}/{epochs} ==========\n")

    # -----------------------------
    # TRAIN
    # -----------------------------
    model.train()

    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (images, labels) in enumerate(train_loader):

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        running_loss += loss.item()

        _, predicted = torch.max(outputs, 1)

        total += labels.size(0)
        correct += (predicted == labels).sum().item()

        if (batch_idx + 1) % 50 == 0 or (batch_idx + 1) == len(train_loader):
            print(
                f"Train Batch [{batch_idx+1}/{len(train_loader)}] "
                f"Loss: {loss.item():.4f}"
            )

    train_loss = running_loss / len(train_loader)
    train_accuracy = 100 * correct / total

    train_loss_history.append(train_loss)
    train_acc_history.append(train_accuracy)

    # -----------------------------
    # VALIDATION
    # -----------------------------
    model.eval()

    val_running_loss = 0.0
    val_correct = 0
    val_total = 0

    with torch.no_grad():

        for images, labels in val_loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(outputs, labels)

            val_running_loss += loss.item()

            _, predicted = torch.max(outputs, 1)

            val_total += labels.size(0)
            val_correct += (predicted == labels).sum().item()

    val_loss = val_running_loss / len(val_loader)
    val_accuracy = 100 * val_correct / val_total

    val_loss_history.append(val_loss)
    val_acc_history.append(val_accuracy)

    print("\nEpoch Summary")
    print(f"Train Loss : {train_loss:.4f}")
    print(f"Train Acc  : {train_accuracy:.2f}%")
    print(f"Val Loss   : {val_loss:.4f}")
    print(f"Val Acc    : {val_accuracy:.2f}%")

    # -----------------------------
    # SAVE BEST MODEL
    # -----------------------------
    if val_accuracy > best_val_accuracy:

        best_val_accuracy = val_accuracy
        best_model_weights = copy.deepcopy(model.state_dict())

        torch.save(best_model_weights, "models/best_resnet50.pth")

        print("✅ Best model updated!")

# -----------------------------
# Save Final Model
# -----------------------------
torch.save(model.state_dict(), "models/final_resnet50.pth")

print("\n================================")
print("Training Complete!")
print(f"Best Validation Accuracy: {best_val_accuracy:.2f}%")
print("Best model saved to:")
print("models/best_resnet50.pth")