from __future__ import annotations

from fastapi import APIRouter, Depends
from PIL import Image

from app.api.deps import get_detector, get_fire, get_flood, upload_image
from app.schemas.responses import (
    DetectResponse,
    FireDetection,
    FireResponse,
    FloodResponse,
    ResourceRecommendation,
)
from app.services.detector import GenericDetector
from app.services.fire import FireDetector
from app.services.flood import FloodSegmenter

router = APIRouter(prefix="/api/v1/detect", tags=["detect"])


@router.post("", response_model=DetectResponse)
def detect_generic(
    image: Image.Image = Depends(upload_image),
    model: GenericDetector = Depends(get_detector),
) -> DetectResponse:
    """Generic object detection (Open Images V7). Counts people / vehicles /
    buildings and estimates real-world footprint via per-class priors."""
    return DetectResponse(**model.analyze(image))


@router.post("/fire", response_model=FireResponse)
def detect_fire(
    image: Image.Image = Depends(upload_image),
    model: FireDetector = Depends(get_fire),
) -> FireResponse:
    """Fire & smoke detection + severity classification + crew recommendation."""
    report = model.analyze(image)
    return FireResponse(
        fire_count=report.fire_count,
        smoke_count=report.smoke_count,
        fire_area_pct=report.fire_area_pct,
        smoke_area_pct=report.smoke_area_pct,
        severity=report.severity,
        estimated_area_m2=report.estimated_area_m2,
        resources=ResourceRecommendation(**report.resources),
        detections=[FireDetection(**d) for d in report.detections],
    )


@router.post("/flood", response_model=FloodResponse)
def detect_flood(
    image: Image.Image = Depends(upload_image),
    model: FloodSegmenter = Depends(get_flood),
) -> FloodResponse:
    """Flood segmentation (YOLOv8n-seg). Returns flooded-pixel percentage and
    counts of buildings / vehicles / people / plants visible in the scene."""
    return FloodResponse(**model.analyze(image))
