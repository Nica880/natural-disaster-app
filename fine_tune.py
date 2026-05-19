import torch
from torchvision import models, datasets, transforms
from torch.utils.data import DataLoader
import os

# Configurare
IMAGES_FOLDER = 'fine_tune_images'  # Creează acest folder cu structura: fine_tune_images/earthquake/, fine_tune_images/flood/, etc.
MODEL_PATH = 'model/disaster_model.pth'
EPOCHS = 10  # Mărit de la 3 la 10
LEARNING_RATE = 0.0001  # Mărit de la 0.00001 la 0.0001
BATCH_SIZE = 4

# Transformări (aceleași ca la training original)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# Verifică dacă folderul există
if not os.path.exists(IMAGES_FOLDER):
    print(f"❌ Creează folderul '{IMAGES_FOLDER}' cu structura:")
    print("  fine_tune_images/")
    print("    ├── earthquake/")
    print("    │   ├── img1.jpg")
    print("    │   └── img2.jpg")
    print("    ├── flood/")
    print("    ├── wildfire/")
    print("    └── etc...")
    exit(1)

# Încarcă imagini
try:
    dataset = datasets.ImageFolder(IMAGES_FOLDER, transform=transform)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    print(f"✅ Încărcat {len(dataset)} imagini din {len(dataset.classes)} clase")
    print(f"   Clase: {dataset.classes}")
except Exception as e:
    print(f"❌ Eroare la încărcare imagini: {e}")
    exit(1)

# Încarcă modelul existent
print(f"\n📦 Încărcare model din {MODEL_PATH}...")
checkpoint = torch.load(MODEL_PATH, map_location='cpu')
model = models.resnet18(pretrained=False)
num_classes = len(checkpoint['classes'])
model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
model.load_state_dict(checkpoint['model'])

print(f"   Clase din model: {checkpoint['classes']}")

# Verifică dacă clasele noi se potrivesc cu cele din model
if set(dataset.classes) != set(checkpoint['classes']):
    print(f"⚠️  WARNING: Clasele din imagini ({dataset.classes}) nu se potrivesc cu cele din model ({checkpoint['classes']})")
    print("   Continuăm oricum, dar verifică maparea claselor!")

# Setează doar ultimul layer pentru antrenare (opțional, pentru fine-tuning mai rapid)
# for param in model.parameters():
#     param.requires_grad = False
# model.fc.requires_grad = True

# Configurare training
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

print(f"\n🚀 Start fine-tuning pe {device}...")
print(f"   Epoci: {EPOCHS}, Learning Rate: {LEARNING_RATE}\n")

# Fine-tuning
model.train()
for epoch in range(EPOCHS):
    epoch_loss = 0
    correct = 0
    total = 0
    
    for batch_idx, (images, labels) in enumerate(dataloader):
        images, labels = images.to(device), labels.to(device)
        
        # Forward pass
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Statistici
        epoch_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        print(f"Epoca {epoch+1}/{EPOCHS} | Batch {batch_idx+1}/{len(dataloader)} | Loss: {loss.item():.4f}", end='\r')
    
    accuracy = 100 * correct / total
    avg_loss = epoch_loss / len(dataloader)
    print(f"Epoca {epoch+1}/{EPOCHS} | Loss: {avg_loss:.4f} | Acuratețe: {accuracy:.2f}%")

# Salvează modelul actualizat
backup_path = MODEL_PATH.replace('.pth', '_backup.pth')
print(f"\n💾 Salvare backup în {backup_path}...")
os.rename(MODEL_PATH, backup_path)

print(f"💾 Salvare model fine-tuned în {MODEL_PATH}...")
torch.save({
    'model': model.state_dict(),
    'classes': checkpoint['classes']
}, MODEL_PATH)

print(f"\n✅ Fine-tuning finalizat!")
print(f"   Backup vechi: {backup_path}")
print(f"   Model nou: {MODEL_PATH}")
print(f"\n🔄 Repornește serverul pentru a folosi modelul nou!")
