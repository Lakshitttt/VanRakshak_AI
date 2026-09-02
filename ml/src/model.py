import torch.nn as nn
from torchvision.models import resnet50, ResNet50_Weights

def create_model(pretrained=True):
    # Load the ResNet50 architecture.
    # During training, the default pretrained=True preserves the original
    # transfer-learning setup. During inference, pretrained=False avoids an
    # unnecessary ImageNet weight download because best_resnet50.pth is loaded
    # immediately afterward.
    weights = ResNet50_Weights.DEFAULT if pretrained else None
    model = resnet50(weights=weights)

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