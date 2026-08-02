from data import train_loader

print("DataLoader created")

images, labels = next(iter(train_loader))

print(images.shape)
print(labels.shape)

print("Success!")