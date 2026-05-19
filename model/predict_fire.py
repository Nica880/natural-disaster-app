"""Run the trained fire model on a single image or a folder.

Usage:
    python model/predict_fire.py path/to/image.jpg
    python model/predict_fire.py path/to/folder/

Outputs detection counts, per-box confidence, total fire-area % of frame,
and the recommended response. Uses the same FireDetector service the API uses,
so the CLI and HTTP results stay consistent.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

# Allow running from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.services.fire import FireDetector  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print("Usage: python model/predict_fire.py <image-or-folder>", file=sys.stderr)
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"Path not found: {target}", file=sys.stderr)
        sys.exit(1)

    settings = get_settings()
    try:
        detector = FireDetector(settings.fire_detector_weights)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    if target.is_dir():
        images = sorted(p for p in target.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    else:
        images = [target]

    for img_path in images:
        img = Image.open(img_path).convert("RGB")
        report = detector.analyze(img)
        print(f"\n{'=' * 60}\n{img_path.name}")
        print(f"  severity   : {report.severity}")
        print(f"  fire boxes : {report.fire_count} ({report.fire_area_pct}% of frame)")
        print(f"  smoke boxes: {report.smoke_count} ({report.smoke_area_pct}% of frame)")
        for d in report.detections:
            print(f"    {d['class']:6s} conf={d['confidence']:.2f}")
        print(f"  recommended response: {report.resources}")


if __name__ == "__main__":
    main()
