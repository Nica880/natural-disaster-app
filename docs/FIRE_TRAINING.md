# Fire detection — training & integration

Goal of this iteration: replace the broken fire path with a real YOLOv8 detector trained on the D-Fire dataset. Targets fire **and** smoke as separate classes so the app can reason about both flame intensity and plume visibility.

## TL;DR

1. Open `notebooks/train_fire_yolo.ipynb` in Google Colab with a free **T4 GPU** runtime.
2. Run all cells. The notebook downloads D-Fire (~21k images), trains YOLOv8s for 50 epochs (~90–120 min), evaluates, and packages `fire.pt`.
3. Drop the resulting `fire.pt` into `model/fire.pt` in this repo (it's gitignored).
4. `pip install -r requirements.txt` locally, then `python model/predict_fire.py path/to/photo.jpg` to test.
5. Start the API: `uvicorn app.main:app --reload`. POST an image to `/api/v1/detect/fire`.

## Dataset

- **D-Fire** — [gaiasd/DFireDataset](https://github.com/gaiasd/DFireDataset), ~21k images, fire+smoke YOLO bbox annotations.
  - Class IDs: `0 = fire`, `1 = smoke`
  - Breakdown: 1,164 fire-only · 5,867 smoke-only · 4,658 both · 9,838 negatives (background)
- Kaggle mirror used by the notebook: [shubhamkarande13/d-fire](https://www.kaggle.com/datasets/shubhamkarande13/d-fire)

## Expected metrics

On the D-Fire test split with the notebook's defaults (YOLOv8s, 50 epochs, AdamW, cosine LR):

| Metric | Expected |
| --- | --- |
| mAP@0.5 | 0.78 – 0.85 |
| mAP@0.5:0.95 | 0.48 – 0.55 |
| Precision (fire) | 0.82 – 0.90 |
| Recall (smoke) | 0.70 – 0.80 |

Smoke recall is usually the weakest number — diffuse smoke plumes are genuinely harder than discrete flames. If smoke recall < 0.6, add 20 more epochs or step up to `yolov8m.pt`.

## Local training (alternative path)

If you want to train on your own Mac:

```bash
# Download D-Fire manually from the GitHub README, organize into the
# images/{train,val,test} + labels/{train,val,test} layout, then:
python model/train_fire.py --data /path/to/dfire/data.yaml --epochs 50 --batch 8
```

The script auto-picks `cuda` → `mps` → `cpu`. On M-series Macs expect ~3–5h. CPU is not viable.

## What gets wired into the app

- `app/services/fire.py` — wraps the trained YOLO with severity classification and a resource-allocation heuristic.
- Endpoint `POST /api/v1/detect/fire` in `app/api/routes/detect.py` returns:
  ```json
  {
    "fire_count": 2,
    "smoke_count": 1,
    "fire_area_pct": 12.4,
    "smoke_area_pct": 30.1,
    "severity": "medium",
    "estimated_area_m2": 1240.0,
    "resources": {
      "fire_trucks": 2, "ambulances": 1, "police_units": 1,
      "aerial_units": 0, "smurd": 1
    },
    "detections": [{ "class": "fire", "confidence": 0.91, "bbox": [...] }, ...]
  }
  ```
- The endpoint gracefully 503s if `model/fire.pt` is missing — the rest of the app keeps running. Check loaded models at `GET /health`.

## Severity heuristic (auditable, simple)

`combined = fire_pct + 0.5 * smoke_pct`

| combined | severity | trucks | ambs | police | aerial | smurd |
| --- | --- | --- | --- | --- | --- | --- |
| < 0.5  | none    | 0 | 0 | 0 | 0 | 0 |
| < 5    | small   | 1 | 0 | 1 | 0 | 0 |
| < 20   | medium  | 2 | 1 | 1 | 0 | 1 |
| < 50   | large   | 4 | 2 | 2 | 1 | 1 |
| ≥ 50   | extreme | 8 | 3 | 4 | 2 | 2 |

Heavy smoke (>30%) in the `large`/`extreme` tier bumps aerial units to ≥2 (visibility tools).

## Area in m² — the assumption you'll need to flag in the thesis

`estimated_area_m2 = (fire_pct / 100) × assumed_frame_area_m2`

The default `assumed_frame_area_m2 = 10000` (= 100 m × 100 m) corresponds to a drone at ~80 m altitude with a 60° horizontal FOV. Real m² needs camera intrinsics + altitude metadata in the upload — that's a follow-up iteration. For now the number is illustrative and the *percentage* is the trustworthy signal.

## Known follow-ups

- Replace ResNet18's 5-epoch training with proper augmentation + 15+ epochs (separate task).
- ~~Fix `area_map` in `/analyze`~~ — done; OIV7 class IDs now correct in `app/services/detector.py`.
- Implement the `/api/v1/drone/upload` endpoint (currently a 501 stub) — token auth + GPS metadata + webhook callback.
- Retrain ResNet18 with proper augmentation and 15+ epochs (current `disaster_model.pth` is from 5 epochs only).
- Add Postgres persistence layer for analysis history.
