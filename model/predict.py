"""Script SIMPLU pentru predicție cu modelul antrenat"""
import torch
from torchvision import models, transforms
from PIL import Image
import sys

# Încarcă model
checkpoint = torch.load('disaster_model.pth', map_location='cpu')
classes = checkpoint['classes']

model = models.resnet18()
model.fc = torch.nn.Linear(model.fc.in_features, len(classes))
model.load_state_dict(checkpoint['model'])
model.eval()

# Transformare
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def predict(image_path):
    """Predictie pe o imagine"""
    img = Image.open(image_path).convert('RGB')
    img_t = transform(img).unsqueeze(0)
    
    with torch.no_grad():
        output = model(img_t)
        probs = torch.nn.functional.softmax(output, dim=1)[0]
        pred_class = probs.argmax().item()
    
    return {
        'class': classes[pred_class],
        'confidence': probs[pred_class].item(),
        'all_probs': {classes[i]: probs[i].item() for i in range(len(classes))}
    }

# Folosire
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Folosire: python3 predict.py <cale_imagine>")
        sys.exit(1)
    
    result = predict(sys.argv[1])
    print(f"\n🎯 Predicție: {result['class']}")
    print(f"📊 Confidence: {result['confidence']:.2%}")
    print(f"\n📈 Toate probabilitățile:")
    for cls, prob in result['all_probs'].items():
        print(f"   {cls}: {prob:.2%}")
