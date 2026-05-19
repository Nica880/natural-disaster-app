"""Car-crash detection service.

Detects accident regions / damaged vehicles in a static image, derives a
severity tier from the number of detections and how much of the frame they
cover, and recommends crew counts. Same auditable-heuristic pattern as the
fire pipeline.

The trained model (weights at `model/carcrash.pt`) is class-name-agnostic:
this service buckets every detection that matches `accident`/`crash`/`severe`
into the same "accident" bin so it works whether the model was trained
with a single `accident` class or with finer-grained classes like
`moderate`/`severe`.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

from app.services._render import annotate_to_data_uri

log = logging.getLogger(__name__)


# Class-name buckets — keyed by substring match against the model's names.
ACCIDENT_PATTERNS = ("accident", "crash", "collision", "wreck", "severe", "moderate", "minor")


def is_accident_class(name: str) -> bool:
    lo = name.lower()
    return any(p in lo for p in ACCIDENT_PATTERNS)


@dataclass
class CarCrashReport:
    accident_count: int
    accident_area_pct: float
    estimated_area_m2: float
    severity: str  # 'none' | 'minor' | 'moderate' | 'major'
    resources: dict
    detections: list
    annotated_image: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def classify_severity(accident_count: int, area_pct: float) -> str:
    if accident_count == 0:
        return "none"
    if accident_count == 1 and area_pct < 8:
        return "minor"
    if accident_count <= 2 and area_pct < 25:
        return "moderate"
    return "major"


_BASE_RESOURCES = {
    "none":     {"ambulances": 0, "police_units": 0, "fire_trucks": 0, "smurd": 0, "tow_trucks": 0},
    "minor":    {"ambulances": 1, "police_units": 1, "fire_trucks": 0, "smurd": 0, "tow_trucks": 1},
    "moderate": {"ambulances": 2, "police_units": 2, "fire_trucks": 1, "smurd": 1, "tow_trucks": 1},
    "major":    {"ambulances": 3, "police_units": 3, "fire_trucks": 2, "smurd": 2, "tow_trucks": 2},
}


def recommend_resources(severity: str, accident_count: int) -> dict:
    base = dict(_BASE_RESOURCES[severity])
    # Multi-vehicle pile-ups → bump tow trucks
    if accident_count >= 4:
        base["tow_trucks"] = max(base["tow_trucks"], accident_count)
    return base


class CarCrashDetector:
    def __init__(self, weights_path: Path, image_size: int = 640, conf: float = 0.25):
        if not weights_path.exists():
            raise FileNotFoundError(
                f"Car-crash model weights missing at {weights_path}. "
                "Train via notebooks/train_carcrash_yolo.ipynb and drop carcrash.pt into model/."
            )
        self.image_size = image_size
        self.conf = conf
        self.model = YOLO(str(weights_path))
        log.info("Car-crash detector loaded: %s (classes=%s)", weights_path, list(self.model.names.values()))

    def analyze(self, image: Image.Image, assumed_frame_area_m2: float = 10_000.0) -> CarCrashReport:
        result = self.model.predict(source=image, conf=self.conf, imgsz=self.image_size, verbose=False)[0]
        h, w = result.orig_shape
        img_area_px = h * w

        accident_area_px = 0.0
        accident_count = 0
        detections = []

        for box in result.boxes:
            cls = int(box.cls[0])
            cls_name = result.names[cls]
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            area_px = (x2 - x1) * (y2 - y1)

            detections.append({
                "class": cls_name,
                "confidence": round(confidence, 3),
                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            })
            if is_accident_class(cls_name):
                accident_area_px += area_px
                accident_count += 1

        area_pct = (accident_area_px / img_area_px) * 100 if img_area_px else 0
        severity = classify_severity(accident_count, area_pct)
        est_m2 = (area_pct / 100.0) * assumed_frame_area_m2

        return CarCrashReport(
            accident_count=accident_count,
            accident_area_pct=round(area_pct, 2),
            estimated_area_m2=round(est_m2, 1),
            severity=severity,
            resources=recommend_resources(severity, accident_count),
            detections=detections,
            annotated_image=annotate_to_data_uri(result),
        )
