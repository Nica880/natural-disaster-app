"""Script SIMPLU pentru antrenarea modelului de detectare dezastre"""
import torch
import torch.nn as nn
from torchvision import models, transforms, datasets
from torch.utils.data import DataLoader
from tqdm import tqdm

# Config
EPOCHS = 5
BATCH_SIZE = 32
DEVICE = 'mps' if torch.backends.mps.is_available() else 'cpu'

print(f"🔧 Device: {DEVICE}")

# Transformări imagini
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# Încarcă date
train_data = datasets.ImageFolder('Natural Disasters/train', transform=transform)
val_data = datasets.ImageFolder('Natural Disasters/valid', transform=transform)

train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_data, batch_size=BATCH_SIZE)

print(f"📊 Train: {len(train_data)} | Valid: {len(val_data)}")
print(f"📂 Clase: {train_data.classes}")

# Model simplu - ResNet18
model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, len(train_data.classes))
model = model.to(DEVICE)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# Antrenare
best_acc = 0
for epoch in range(EPOCHS):
    print(f"\n📍 Epoca {epoch+1}/{EPOCHS}")
    
    # Train
    model.train()
    train_loss, correct = 0, 0
    for imgs, labels in tqdm(train_loader, desc="Train"):
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        train_loss += loss.item()
        correct += (outputs.argmax(1) == labels).sum().item()
    
    train_acc = correct / len(train_data)
    print(f"Train Loss: {train_loss/len(train_loader):.3f} | Acc: {train_acc:.3f}")
    
    # Validation
    model.eval()
    correct = 0
    with torch.no_grad():
        for imgs, labels in tqdm(val_loader, desc="Valid"):
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            outputs = model(imgs)
            correct += (outputs.argmax(1) == labels).sum().item()
    
    val_acc = correct / len(val_data)
    print(f"Valid Acc: {val_acc:.3f}")
    
    # Salvează cel mai bun
    if val_acc > best_acc:
        best_acc = val_acc
        torch.save({
            'model': model.state_dict(),
            'classes': train_data.classes,
            'accuracy': best_acc
        }, 'disaster_model.pth')
        print(f"✅ Model salvat! Acc: {best_acc:.3f}")

print(f"\n✅ Antrenare completă! Best accuracy: {best_acc:.3f}")
