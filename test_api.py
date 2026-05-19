import requests

image_path = "Natural Disasters/test/Flood/0_jpg.rf.bb6e1fdbe841a97705cf4788659f7818.jpg"

with open(image_path, "rb") as f:
    response = requests.post("http://127.0.0.1:8000/predict", files={"file": f})

result = response.json()

print(f"Image: {image_path}")
print(f"Predicted: {result['class']}")
print(f"Confidence: {result['confidence']:.2%}")
print("\nAll probabilities:")
for cls, prob in result['probabilities'].items():
    print(f"  {cls}: {prob:.2%}")
