"""Run the trained fire model on a single image or a folder.

Usage:
    python model/predict_fire.py path/to/image.jpg
    python model/predict_fire.py path/to/folder/

Outputs detection counts, per-box confidence, total fire-area % of frame,
and saves an annotated image next to each input.
"""
from __future__ import annotations

import sys
from pathlib import Path

from ultralytics import YOLO

WEIGHTS = Path(__file__).parent / "fire.pt"
NAMES = {0: "fire", 1: "smoke"}


def analyze(model: YOLO, image_path: Path) -> dict:
    result = model.predict(source=str(image_path), conf=0.25, imgsz=640, save=True, verbose=False)[0]
    h, w = result.orig_shape
    img_area = h * w

    fire_area = smoke_area = 0.0
    fire_count = smoke_count = 0
    detections = []

    for box in result.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        area = (x2 - x1) * (y2 - y1)
        detections.append({"class": NAMES[cls], "confidence": round(conf, 3), "area_px": round(area, 1)})
        if cls == 0:
            fire_area += area
            fire_count += 1
        elif cls == 1:
            smoke_area += area
            smoke_count += 1

    return {
        "image": str(image_path),
        "fire_count": fire_count,
        "smoke_count": smoke_count,
        "fire_area_pct": round(fire_area / img_area * 100, 2),
        "smoke_area_pct": round(smoke_area / img_area * 100, 2),
        "detections": detections,
        "annotated_image": str(Path(result.save_dir) / image_path.name),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python model/predict_fire.py <image-or-folder>", file=sys.stderr)
        sys.exit(1)
    if not WEIGHTS.exists():
        print(f"Trained weights missing at {WEIGHTS}. Run training first (see notebooks/train_fire_yolo.ipynb).", file=sys.stderr)
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"Path not found: {target}", file=sys.stderr)
        sys.exit(1)

    model = YOLO(str(WEIGHTS))

    if target.is_dir():
        images = [p for p in target.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    else:
        images = [target]

    for img in images:
        report = analyze(model, img)
        print(f"\n{'=' * 60}\n{img.name}")
        print(f"  fire boxes : {report['fire_count']} ({report['fire_area_pct']}% of frame)")
        print(f"  smoke boxes: {report['smoke_count']} ({report['smoke_area_pct']}% of frame)")
        for d in report["detections"]:
            print(f"    {d['class']:6s} conf={d['confidence']:.2f}")
        print(f"  annotated -> {report['annotated_image']}")


if __name__ == "__main__":
    main()
