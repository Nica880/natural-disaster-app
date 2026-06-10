"""End-to-end accuracy audit: run the REAL production pipeline (classifier +
specialists + verdict logic) over the camera simulator's ground-truth frames
(folder name = true label) and print a confusion matrix + per-class accuracy +
the exact list of misclassified frames. No DB writes, no incidents created.

Run on the host:         python model/audit_pipeline.py
Run inside the backend:  docker cp camera_sim/samples raid-backend:/tmp/audit_samples
                         docker cp model/audit_pipeline.py raid-backend:/tmp/
                         docker exec -e PYTHONPATH=/app raid-backend python /tmp/audit_pipeline.py

Measured history on the 120-frame set (24 x 5 cameras):
  v1 classifier, no guards .......................  98/120 (81.7%)
  + override/evidence guards in analyze.py ....... 103/120 (85.8%)
  + v2 classifier (train_v2.py, 99.2% test) ...... 115/120 (95.8%)
  + HIGH_CONFIDENCE_THRESHOLD recalibrated 0.75 .. 119/120 (99.2%, 0 wrong-type)
"""
import sys
import warnings
import logging
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings("ignore")
logging.getLogger("ultralytics").setLevel(logging.ERROR)

# Importable both from the repo root (host) and from /tmp inside the container.
_HERE = Path(__file__).resolve().parent
for cand in (_HERE.parent, Path("/app")):
    if (cand / "app").is_dir():
        sys.path.insert(0, str(cand))
        break

from PIL import Image                              # noqa: E402
from app.config import get_settings                # noqa: E402
from app.api.deps import ModelRegistry, MAX_IMAGE_SIDE  # noqa: E402
from app.api.routes.analyze import analyze         # noqa: E402

GT = {
    "cam-accident":   "Car Crash",
    "cam-cyclone":    "Cyclone",
    "cam-earthquake": "Earthquake",
    "cam-fire":       "Wildfire",
    "cam-flood":      "Flood",
}

# Container layout first, host repo layout as fallback.
for root in (Path("/tmp/audit_samples"), _HERE.parent / "camera_sim" / "samples"):
    if root.is_dir():
        ROOT = root
        break
else:
    sys.exit("No sample frames found (looked in /tmp/audit_samples and camera_sim/samples).")

reg = ModelRegistry(get_settings())
reg.classifier(); reg.detector(); reg.fire(); reg.flood(); reg.carcrash()

confusion = defaultdict(lambda: defaultdict(int))
misses = []
total = 0

print("================ PER-IMAGE ================", flush=True)
for cam, truth in GT.items():
    for fp in sorted((ROOT / cam).glob("frame_*.jpg")):
        total += 1
        try:
            img = Image.open(fp).convert("RGB")
            if max(img.size) > MAX_IMAGE_SIDE:
                img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
            res = analyze(img, reg)
            v, clf = res.verdict, res.classification
            confusion[truth][v.disaster_type] += 1
            mark = "OK " if v.disaster_type == truth else "XXX"
            print(f"{mark} {cam:14s} {fp.name:13s} truth={truth:11s} "
                  f"clf={clf.predicted_class:11s}({clf.confidence:.2f}) "
                  f"-> verdict={v.disaster_type:11s} [{v.primary_model}]", flush=True)
            if v.disaster_type != truth:
                probs = sorted(clf.probabilities.items(), key=lambda kv: kv[1], reverse=True)[:3]
                probs_s = ", ".join(f"{k} {p * 100:.0f}%" for k, p in probs)
                misses.append((cam, fp.name, truth, v.disaster_type,
                               clf.predicted_class, clf.confidence, v.primary_model, probs_s))
        except Exception as e:  # noqa: BLE001 — audit must survive a bad frame
            confusion[truth]["ERROR"] += 1
            print(f"ERR {cam:14s} {fp.name:13s} truth={truth:11s} EXCEPTION: {e}", flush=True)
            misses.append((cam, fp.name, truth, "ERROR", str(e), 0.0, "none", ""))

labels = ["Car Crash", "Cyclone", "Earthquake", "Wildfire", "Flood", "Uncertain"]
print("\n================ CONFUSION MATRIX (rows=truth, cols=verdict) ================")
print("truth \\ verdict".ljust(14) + "".join(l[:9].rjust(11) for l in labels))
for truth in GT.values():
    print(truth.ljust(14) + "".join(str(confusion[truth].get(v, 0)).rjust(11) for v in labels))

print("\n================ PER-CLASS ACCURACY ================")
correct_total = 0
for truth in GT.values():
    n = sum(confusion[truth].values())
    c = confusion[truth].get(truth, 0)
    correct_total += c
    print(f"  {truth:12s}: {c}/{n}  = {100.0 * c / n if n else 0:5.1f}%")
print(f"  {'OVERALL':12s}: {correct_total}/{total} = {100.0 * correct_total / total:5.1f}%")

print("\n================ MISCLASSIFIED FRAMES (look at these) ================")
for cam, frame, truth, vtype, clf, conf, pm, probs in misses:
    print(f"  {cam}/{frame}: TRUTH={truth} -> VERDICT={vtype}  "
          f"(classifier={clf} {conf:.2f}, primary={pm}) | top3: {probs}")
print(f"\nTOTAL MISSES: {len(misses)}/{total}")
