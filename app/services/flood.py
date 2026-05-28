"""Flood segmentation service.

Works with both class vocabularies:
  - legacy 6-class (Flood Amateur Video):  flood / building / plant / person / vehicle / sky
  - FloodNet 10-class:                     background / building_flooded / building_non-flooded /
                                           road_flooded / road_non-flooded / water / tree /
                                           vehicle / pool / grass

Classes are matched by name pattern rather than fixed IDs so the same code
serves whichever model weights happen to be loaded.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

from app.services._render import annotate_to_data_uri

log = logging.getLogger(__name__)


# Pattern → bucket. Lowercased substring match against the model's class names.
GROUP_PATTERNS: dict[str, tuple[str, ...]] = {
    "flooded":  ("flood", "water", "flooded"),
    "building": ("building",),
    "vehicle":  ("vehicle", "car"),
    "person":   ("person", "people", "human"),
    "plant":    ("tree", "plant", "grass", "vegetation", "pool"),
}


def _bucket(cls_name: str) -> str | None:
    """Return the first matching bucket for a class name, else None."""
    lo = cls_name.lower()
    for bucket, patterns in GROUP_PATTERNS.items():
        if any(p in lo for p in patterns):
            return bucket
    return None


@dataclass
class FloodReport:
    flood_area_pct: float
    flood_area_m2: float
    buildings: int
    vehicles: int
    people: int
    plants: int
    total_objects: int
    class_counts: dict[str, int] = field(default_factory=dict)


# Severity tiers + baseline resource recommendations.  Mirrors the pattern in
# app/services/fire.py — intentionally coarse and auditable; this is a demo,
# not a real dispatch system.

def classify_flood_severity(area_pct: float, people: int, buildings: int) -> str:
    score = area_pct + 4 * min(people, 10) + 2 * min(buildings, 10)
    if score < 2:   return "none"
    if score < 12:  return "minor"
    if score < 35:  return "moderate"
    if score < 65:  return "major"
    return "catastrophic"


_FLOOD_BASE_RESOURCES = {
    "none":         {"boats": 0, "ambulances": 0, "evacuation_buses": 0, "police_units": 0, "smurd": 0},
    "minor":        {"boats": 1, "ambulances": 0, "evacuation_buses": 0, "police_units": 1, "smurd": 0},
    "moderate":     {"boats": 2, "ambulances": 1, "evacuation_buses": 1, "police_units": 1, "smurd": 1},
    "major":        {"boats": 4, "ambulances": 2, "evacuation_buses": 2, "police_units": 2, "smurd": 1},
    "catastrophic": {"boats": 8, "ambulances": 4, "evacuation_buses": 4, "police_units": 4, "smurd": 2},
}


def recommend_flood_resources(severity: str, people: int) -> dict:
    base = dict(_FLOOD_BASE_RESOURCES[severity])
    # Scale ambulances + evacuation buses up if many people are in-frame.
    if people > 5 and severity != "none":
        base["ambulances"]       = max(base["ambulances"],       people // 3)
        base["evacuation_buses"] = max(base["evacuation_buses"], people // 10)
    return base


class FloodSegmenter:
    def __init__(self, weights_path: Path, image_size: int = 640, conf: float = 0.25):
        if not weights_path.exists():
            raise FileNotFoundError(f"Flood weights missing at {weights_path}")
        self.image_size = image_size
        self.conf = conf
        self.model = YOLO(str(weights_path))
        log.info("Flood segmenter loaded: %s (classes=%s)", weights_path, list(self.model.names.values()))

    def analyze(self, image: Image.Image, assumed_frame_area_m2: float = 10_000.0) -> dict:
        results = self.model.predict(source=image, imgsz=self.image_size, conf=self.conf, verbose=False)[0]

        flood_area_pct = 0.0
        counts: dict[str, int] = {"flooded": 0, "building": 0, "vehicle": 0, "person": 0, "plant": 0}
        class_counts: dict[str, int] = {}

        if results.masks is not None and results.boxes is not None:
            img_area = image.width * image.height
            for mask, cls_id in zip(results.masks.data, results.boxes.cls):
                cls_name = results.names[int(cls_id)]
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                bucket = _bucket(cls_name)
                if bucket:
                    counts[bucket] = counts.get(bucket, 0) + 1
                if bucket == "flooded":
                    flood_area_pct += (mask.sum().item() / img_area) * 100

        total = sum(class_counts.values())
        flood_m2 = (flood_area_pct / 100.0) * assumed_frame_area_m2
        severity = classify_flood_severity(flood_area_pct, counts["person"], counts["building"])
        resources = recommend_flood_resources(severity, counts["person"])

        return {
            "flood_area_pct":  round(flood_area_pct, 2),
            "flood_area_m2":   round(flood_m2, 1),
            "severity":        severity,
            "resources":       resources,
            "buildings":       counts["building"],
            "vehicles":        counts["vehicle"],
            "people":          counts["person"],
            "plants":          counts["plant"],
            "total_objects":   total,
            "class_counts":    class_counts,
            "annotated_image": annotate_to_data_uri(results),
        }
