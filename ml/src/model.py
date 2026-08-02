import torch.nn as nn
from torchvision.models import resnet50, ResNet50_Weights

def create_model():
    # Load pretrained ResNet50
    model = resnet50(weights=ResNet50_Weights.DEFAULT)

    # Freeze all pretrained layers
    for param in model.parameters():
        param.requires_grad = False

    # Replace final layer for our 10 classes
    model.fc = nn.Sequential(
        nn.Linear(model.fc.in_features, 512),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(512, 10)
    )

    return model


if __name__ == "__main__":
    model = create_model()
    print(model)