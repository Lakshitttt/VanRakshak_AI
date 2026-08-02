from torchvision import datasets, transforms
from torch.utils.data import random_split, DataLoader
import torch

# -----------------------------
# Dataset Path
# -----------------------------
DATASET_PATH = r"L:\Satellite_Deforestation_Project\dataset\EuroSAT"

# -----------------------------
# Image Transformations
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
# Load Dataset
# -----------------------------
dataset = datasets.ImageFolder(
    DATASET_PATH,
    transform=transform
)

classes = dataset.classes

# -----------------------------
# Dataset Split (70/15/15)
# -----------------------------
train_size = int(0.70 * len(dataset))
val_size = int(0.15 * len(dataset))
test_size = len(dataset) - train_size - val_size

# Fixed seed for reproducibility
generator = torch.Generator().manual_seed(42)

train_set, val_set, test_set = random_split(
    dataset,
    [train_size, val_size, test_size],
    generator=generator
)

# -----------------------------
# DataLoaders
# -----------------------------
train_loader = DataLoader(
    train_set,
    batch_size=32,
    shuffle=True,
    num_workers=0,
    pin_memory=True
)

val_loader = DataLoader(
    val_set,
    batch_size=32,
    shuffle=False,
    num_workers=0,
    pin_memory=True
)

test_loader = DataLoader(
    test_set,
    batch_size=32,
    shuffle=False,
    num_workers=0,
    pin_memory=True
)