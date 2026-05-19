"""Generic object detector (YOLOv8 trained on Open Images V7). Counts
people / vehicles / buildings and estimates real-world footprint via
per-class priors. NOT fire-specific — see services.fire for that.
"""
from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

from app.services._render import annotate_to_data_uri

log = logging.getLogger(__name__)


# Open Images V7 class IDs. The previous implementation used COCO IDs
# against an OIV7 model — see git history for the broken version.
OIV7_AREA_PRIORS_M2: dict[int, float] = {
    381: 0.7,   # Person
    90:  12,    # Car
    73:  30,    # Bus
    558: 25,    # Truck
    564: 18,    # Van
    342: 2,     # Motorcycle
    42:  1.5,   # Bicycle
    52:  20,    # Boat
    257: 100,   # House
    70:  150,   # Building
    354: 250,   # Office building
    553: 12,    # Tree
    364: 15,    # Palm tree
    530: 6,     # Tent
    6:   25,    # Ambulance
}
OIV7_VEHICLE_IDS = {90, 73, 558, 564, 342, 42, 52, 223, 6}
OIV7_PERSON_IDS = {381}
OIV7_BUILDING_IDS = {70, 257, 354}


class GenericDetector:
    def __init__(self, weights_path: Path, image_size: int = 640, conf: float = 0.25):
        self.image_size = image_size
        self.conf = conf
        self.model = YOLO(str(weights_path))
        log.info("Generic detector loaded: %s", weights_path)

    def analyze(self, image: Image.Image) -> dict:
        results = self.model.predict(source=image, imgsz=self.image_size, conf=self.conf, verbose=False)[0]
        boxes = results.boxes

        class_counts: dict[str, int] = {}
        vehicles = people = buildings = 0
        estimated_area_m2 = 0.0
        total_box_area_px = 0.0

        for box in boxes:
            cls_id = int(box.cls[0])
            cls_name = results.names[cls_id]
            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            total_box_area_px += (x2 - x1) * (y2 - y1)

            if cls_id in OIV7_VEHICLE_IDS:
                vehicles += 1
            if cls_id in OIV7_PERSON_IDS:
                people += 1
            if cls_id in OIV7_BUILDING_IDS:
                buildings += 1
            estimated_area_m2 += OIV7_AREA_PRIORS_M2.get(cls_id, 0)

        img_area_px = image.width * image.height
        area_percent = (total_box_area_px / img_area_px) * 100 if img_area_px else 0

        return {
            "vehicles": vehicles,
            "people": people,
            "buildings": buildings,
            "area_percent": round(area_percent, 2),
            "estimated_area_m2": round(estimated_area_m2, 1),
            "objects_detected": len(boxes),
            "class_counts": class_counts,
            "annotated_image": annotate_to_data_uri(results),
        }
