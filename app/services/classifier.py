"""ResNet18 disaster-type classifier (5 classes: Car Crash / Cyclone /
Earthquake / Flood / Wildfire). Trained via model/train.py.
"""
from __future__ import annotations

import logging
from pathlib import Path

import torch
from PIL import Image
from torchvision import models, transforms

log = logging.getLogger(__name__)


class DisasterClassifier:
    def __init__(self, weights_path: Path, image_size: int = 224, device: str | None = None):
        self.weights_path = weights_path
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        checkpoint = torch.load(weights_path, map_location=self.device)
        self.classes: list[str] = checkpoint["classes"]

        model = models.resnet18()
        model.fc = torch.nn.Linear(model.fc.in_features, len(self.classes))
        model.load_state_dict(checkpoint["model"])
        model.eval().to(self.device)
        self.model = model

        self.transform = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
        log.info("Classifier loaded: %s (classes=%s)", weights_path, self.classes)

    def predict(self, image: Image.Image) -> dict:
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.nn.functional.softmax(logits, dim=1)[0]
            idx = int(probs.argmax())
        return {
            "predicted_class": self.classes[idx],
            "confidence": float(probs[idx]),
            "probabilities": {c: float(probs[i]) for i, c in enumerate(self.classes)},
        }
