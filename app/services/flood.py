"""Flood segmentation service — YOLOv8n-seg fine-tuned on the Flood
Amateur Video for Semantic Segmentation Dataset. Classes: flood,
building, plant, person, vehicle, sky.
"""
from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

log = logging.getLogger(__name__)


class FloodSegmenter:
    def __init__(self, weights_path: Path, image_size: int = 640, conf: float = 0.25):
        self.image_size = image_size
        self.conf = conf
        self.model = YOLO(str(weights_path))
        log.info("Flood segmenter loaded: %s", weights_path)

    def analyze(self, image: Image.Image) -> dict:
        results = self.model.predict(source=image, imgsz=self.image_size, conf=self.conf, verbose=False)[0]

        flood_area_pct = 0.0
        class_counts: dict[str, int] = {}

        if results.masks is not None and results.boxes is not None:
            img_area = image.width * image.height
            for mask, cls_id in zip(results.masks.data, results.boxes.cls):
                cls_name = results.names[int(cls_id)]
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                if cls_name == "flood":
                    flood_area_pct += (mask.sum().item() / img_area) * 100

        return {
            "flood_area_pct": round(flood_area_pct, 2),
            "flood_area_m2": round(flood_area_pct * 100, 1),  # 1% ≈ 100m² placeholder
            "buildings": class_counts.get("building", 0),
            "vehicles": class_counts.get("vehicle", 0),
            "people": class_counts.get("person", 0),
            "plants": class_counts.get("plant", 0),
            "total_objects": len(results.boxes) if results.boxes is not None else 0,
        }
