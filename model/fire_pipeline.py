"""Fire analysis pipeline — combines the trained fire YOLO with a resource-
allocation heuristic. Used by app.py's /fire_analysis endpoint and by CLI tools.

Assumptions documented inline. The heuristic is intentionally simple and
auditable; it's meant for a didactic demo, not life-safety decisions.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from PIL import Image
from ultralytics import YOLO


FIRE_WEIGHTS = Path(__file__).parent / "fire.pt"
GENERIC_WEIGHTS_FALLBACK = Path(__file__).parent.parent / "yolov8n-oiv7.pt"


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


def recommend_resources(severity: str, fire_pct: float, smoke_pct: float) -> dict:
    """Heuristic resource recommendation.

    Caveat: real dispatching depends on terrain, wind, water access, etc.
    This is a coarse mapping from area-coverage to crew counts that gives
    the demo something defensible to show.
    """
    base = {
        "none":    {"fire_trucks": 0, "ambulances": 0, "police_units": 0, "aerial_units": 0, "smurd": 0},
        "small":   {"fire_trucks": 1, "ambulances": 0, "police_units": 1, "aerial_units": 0, "smurd": 0},
        "medium":  {"fire_trucks": 2, "ambulances": 1, "police_units": 1, "aerial_units": 0, "smurd": 1},
        "large":   {"fire_trucks": 4, "ambulances": 2, "police_units": 2, "aerial_units": 1, "smurd": 1},
        "extreme": {"fire_trucks": 8, "ambulances": 3, "police_units": 4, "aerial_units": 2, "smurd": 2},
    }[severity]
    # Smoke heavy → bias toward aerial visibility tools
    if smoke_pct > 30 and severity in {"large", "extreme"}:
        base["aerial_units"] = max(base["aerial_units"], 2)
    return base


@dataclass
class FirePipeline:
    weights: Path = FIRE_WEIGHTS
    px_per_m2: float = 1.0  # placeholder — see analyze() for the area assumption

    def __post_init__(self):
        if not self.weights.exists():
            raise FileNotFoundError(
                f"Fire model weights missing at {self.weights}. "
                "Train the model first (see notebooks/train_fire_yolo.ipynb), then "
                "drop the resulting fire.pt into model/."
            )
        self.model = YOLO(str(self.weights))
        self.names = {0: "fire", 1: "smoke"}

    def analyze(self, image: Image.Image, assumed_frame_area_m2: float = 10_000.0) -> FireReport:
        """Run fire/smoke detection and produce a structured report.

        `assumed_frame_area_m2` is the *real-world* ground area the photo
        covers. Default 10000 m² (= 100m × 100m, typical for a drone at
        ~80m altitude with a 60° FOV). Pass the actual value if you have
        camera intrinsics + altitude metadata; otherwise the m² number
        is illustrative.
        """
        result = self.model.predict(source=image, conf=0.25, imgsz=640, verbose=False)[0]
        h, w = result.orig_shape
        img_area_px = h * w

        fire_area_px = smoke_area_px = 0.0
        fire_count = smoke_count = 0
        detections = []

        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            area_px = (x2 - x1) * (y2 - y1)
            detections.append({
                "class": self.names[cls],
                "confidence": round(conf, 3),
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
        # Area in m² assumes the whole frame == assumed_frame_area_m2
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
        )
