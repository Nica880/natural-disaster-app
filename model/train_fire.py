"""Train YOLOv8 fire+smoke detector on D-Fire.

Usage (local):
    python model/train_fire.py --data /path/to/dfire/data.yaml --epochs 50

Mirrors the Colab notebook. Use the notebook if you don't have a local GPU —
training on CPU is infeasible (>24h). Mac M-series MPS works but is ~3-5x
slower than a Colab T4.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from ultralytics import YOLO


def pick_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "0"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to D-Fire data.yaml")
    parser.add_argument("--weights", default="yolov8s.pt", help="Starting weights")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16, help="Batch size — drop to 8 on Mac")
    parser.add_argument("--device", default="auto", help="auto | mps | cpu | 0")
    parser.add_argument("--name", default="fire_yolov8s")
    parser.add_argument("--patience", type=int, default=15)
    args = parser.parse_args()

    if not Path(args.data).exists():
        print(f"data.yaml not found: {args.data}", file=sys.stderr)
        sys.exit(1)

    device = pick_device(args.device)
    print(f"Device: {device}")

    model = YOLO(args.weights)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        close_mosaic=10,
        optimizer="AdamW",
        lr0=0.001,
        cos_lr=True,
        name=args.name,
        device=device,
        workers=2,
        seed=42,
        verbose=True,
    )

    print(f"Done. Best weights: runs/detect/{args.name}/weights/best.pt")


if __name__ == "__main__":
    main()
