"""Fire & smoke detection service — YOLOv8s trained on D-Fire (21k images,
fire + smoke bbox annotations). Combines detection with a severity heuristic
and a coarse resource-allocation recommendation.

The severity tiers and crew counts are intentionally simple/auditable —
this is a didactic demo, not a real dispatch system.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

from app.services._render import annotate_to_data_uri

log = logging.getLogger(__name__)


@dataclass
class FireReport:
    fire_count: int
    smoke_count: int
    fire_area_pct: float
    smoke_area_pct: float
    severity: str  # 'none' | 'small' | 'medium' | 'large' | 'extreme'
    estimated_area_m2: float
    resources: dict
    detections: list
    annotated_image: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def classify_severity(fire_pct: float, smoke_pct: float) -> str:
    combined = fire_pct + 0.5 * smoke_pct
    if combined < 0.5:
        return "none"
    if combined < 5:
        return "small"
    if combined < 20:
        return "medium"
    if combined < 50:
        return "large"
    return "extreme"


_BASE_RESOURCES = {
    "none":    {"fire_trucks": 0, "ambulances": 0, "police_units": 0, "aerial_units": 0, "smurd": 0},
    "small":   {"fire_trucks": 1, "ambulances": 0, "police_units": 1, "aerial_units": 0, "smurd": 0},
    "medium":  {"fire_trucks": 2, "ambulances": 1, "police_units": 1, "aerial_units": 0, "smurd": 1},
    "large":   {"fire_trucks": 4, "ambulances": 2, "police_units": 2, "aerial_units": 1, "smurd": 1},
    "extreme": {"fire_trucks": 8, "ambulances": 3, "police_units": 4, "aerial_units": 2, "smurd": 2},
}


def recommend_resources(severity: str, fire_pct: float, smoke_pct: float) -> dict:
    base = dict(_BASE_RESOURCES[severity])
    # Heavy smoke → bias toward aerial visibility tools
    if smoke_pct > 30 and severity in {"large", "extreme"}:
        base["aerial_units"] = max(base["aerial_units"], 2)
    return base


class FireDetector:
    NAMES = {0: "fire", 1: "smoke"}

    def __init__(self, weights_path: Path, image_size: int = 640, conf: float = 0.25):
        if not weights_path.exists():
            raise FileNotFoundError(
                f"Fire model weights missing at {weights_path}. "
                "Train via notebooks/train_fire_yolo.ipynb and drop fire.pt into model/."
            )
        self.image_size = image_size
        self.conf = conf
        self.model = YOLO(str(weights_path))
        log.info("Fire detector loaded: %s", weights_path)

    def analyze(self, image: Image.Image, assumed_frame_area_m2: float = 10_000.0) -> FireReport:
        """Run inference and produce a structured report.

        `assumed_frame_area_m2` is the real-world ground area the photo
        covers (default ≈ drone at 80m / 60° FOV). Pass the actual value
        when camera intrinsics + altitude are available; the percentage
        is the trustworthy signal regardless.
        """
        result = self.model.predict(source=image, conf=self.conf, imgsz=self.image_size, verbose=False)[0]
        h, w = result.orig_shape
        img_area_px = h * w

        fire_area_px = smoke_area_px = 0.0
        fire_count = smoke_count = 0
        detections = []

        for box in result.boxes:
            cls = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            area_px = (x2 - x1) * (y2 - y1)
            detections.append({
                "class": self.NAMES[cls],
                "confidence": round(confidence, 3),
                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            })
            if cls == 0:
                fire_area_px += area_px
                fire_count += 1
            elif cls == 1:
                smoke_area_px += area_px
                smoke_count += 1

        fire_pct = (fire_area_px / img_area_px) * 100 if img_area_px else 0
        smoke_pct = (smoke_area_px / img_area_px) * 100 if img_area_px else 0
        severity = classify_severity(fire_pct, smoke_pct)
        est_m2 = (fire_pct / 100.0) * assumed_frame_area_m2

        return FireReport(
            fire_count=fire_count,
            smoke_count=smoke_count,
            fire_area_pct=round(fire_pct, 2),
            smoke_area_pct=round(smoke_pct, 2),
            severity=severity,
            estimated_area_m2=round(est_m2, 1),
            resources=recommend_resources(severity, fire_pct, smoke_pct),
            detections=detections,
            annotated_image=annotate_to_data_uri(result),
        )
