import copy
import torch
import torch.nn as nn
import torch.optim as optim

from ml.src.model import create_finetune_model
from ml.src.data import train_loader, val_loader


# ------------------------------------------------------------
# Device
# ------------------------------------------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"\nUsing Device: {device}")


# ------------------------------------------------------------
# Model
# ------------------------------------------------------------

model = create_finetune_model().to(device)

print("ResNet50 fine-tuning model loaded successfully!\n")

# Show trainable parameters
trainable_params = sum(
    p.numel() for p in model.parameters()
    if p.requires_grad
)

total_params = sum(
    p.numel() for p in model.parameters()
)

print(f"Trainable parameters: {trainable_params:,}")
print(f"Total parameters:     {total_params:,}")


# ------------------------------------------------------------
# Loss
# ------------------------------------------------------------

criterion = nn.CrossEntropyLoss()


# ------------------------------------------------------------
# Optimizer
# ------------------------------------------------------------

optimizer = optim.Adam(
    filter(lambda p: p.requires_grad, model.parameters()),
    lr=1e-4
)


# ------------------------------------------------------------
# Training configuration
# ------------------------------------------------------------

epochs = 10

best_val_accuracy = 0.0
best_model_weights = copy.deepcopy(model.state_dict())


# ------------------------------------------------------------
# Training
# ------------------------------------------------------------

for epoch in range(epochs):

    print(f"\n========== Epoch {epoch + 1}/{epochs} ==========\n")

    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

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
                f"Train Batch [{batch_idx + 1}/{len(train_loader)}] "
                f"Loss: {loss.item():.4f}"
            )

    train_loss = running_loss / len(train_loader)
    train_accuracy = 100 * correct / total

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

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

    print("\nEpoch Summary")
    print(f"Train Loss : {train_loss:.4f}")
    print(f"Train Acc  : {train_accuracy:.2f}%")
    print(f"Val Loss   : {val_loss:.4f}")
    print(f"Val Acc    : {val_accuracy:.2f}%")

    # --------------------------------------------------------
    # SAVE BEST FINE-TUNED MODEL
    # --------------------------------------------------------

    if val_accuracy > best_val_accuracy:

        best_val_accuracy = val_accuracy
        best_model_weights = copy.deepcopy(model.state_dict())

        torch.save(
            best_model_weights,
            "../models/indian_resnet50_finetuned.pth"
        )

        print("✅ Best fine-tuned model updated!")


print("\n================================")
print("Fine-Tuning Complete!")
print(f"Best Validation Accuracy: {best_val_accuracy:.2f}%")
print("Best model saved to:")
print("../models/indian_resnet50_finetuned.pth")