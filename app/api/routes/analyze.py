"""Unified auto-analysis endpoint.

A single POST runs the scene classifier + every available specialist
detector + the generic object detector, then builds a `Verdict` — the
one-line headline the operator should see. Unavailable models are
silently skipped (the verdict notes them).

Specialists are matched to the classifier's prediction:
  Wildfire    → fire detector       (severity, fire/smoke %, m², crews)
  Flood       → flood segmenter     (flooded %, m², buildings/vehicles)
  Car Crash   → carcrash detector   (severity, count, crews)
  Cyclone /   → generic detector    (no specialist; report people/vehicles/buildings)
  Earthquake

If the classifier's confidence is below `LOW_CONFIDENCE_THRESHOLD` or the
specialist contradicts it (e.g. classifier says Wildfire but fire detector
found no fire boxes), the verdict downgrades to "Uncertain" with a note.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from PIL import Image

from app.api.deps import ModelRegistry, get_registry, upload_image
from app.schemas.responses import (
    AnalyzeResponse,
    CarCrashDetection,
    CarCrashResourceRecommendation,
    CarCrashResponse,
    ClassifyResponse,
    DetectResponse,
    FireDetection,
    FireResponse,
    FloodResponse,
    ResourceRecommendation,
    Verdict,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["analyze"])

LOW_CONFIDENCE_THRESHOLD = 0.45


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    image: Image.Image = Depends(upload_image),
    reg: ModelRegistry = Depends(get_registry),
) -> AnalyzeResponse:
    if reg.classifier() is None:
        raise HTTPException(503, "Classifier not loaded — cannot run unified analysis.")

    # ── 1. Classify the scene ─────────────────────────────────────────────
    classify_dict = reg.classifier().predict(image)
    classification = ClassifyResponse(**classify_dict)

    # ── 2. Run every loaded specialist ────────────────────────────────────
    fire_resp = flood_resp = carcrash_resp = generic_resp = None

    if reg.detector() is not None:
        generic_resp = DetectResponse(**reg.detector().analyze(image))

    if reg.fire() is not None:
        f = reg.fire().analyze(image)
        fire_resp = FireResponse(
            fire_count=f.fire_count, smoke_count=f.smoke_count,
            fire_area_pct=f.fire_area_pct, smoke_area_pct=f.smoke_area_pct,
            severity=f.severity, estimated_area_m2=f.estimated_area_m2,
            resources=ResourceRecommendation(**f.resources),
            detections=[FireDetection(**d) for d in f.detections],
            annotated_image=f.annotated_image,
        )

    if reg.flood() is not None:
        flood_resp = FloodResponse(**reg.flood().analyze(image))

    if reg.carcrash() is not None:
        c = reg.carcrash().analyze(image)
        carcrash_resp = CarCrashResponse(
            accident_count=c.accident_count,
            accident_area_pct=c.accident_area_pct,
            estimated_area_m2=c.estimated_area_m2,
            severity=c.severity,
            resources=CarCrashResourceRecommendation(**c.resources),
            detections=[CarCrashDetection(**d) for d in c.detections],
            annotated_image=c.annotated_image,
        )

    # ── 3. Build the verdict ──────────────────────────────────────────────
    verdict = _build_verdict(classification, fire_resp, flood_resp, carcrash_resp, generic_resp)

    return AnalyzeResponse(
        verdict=verdict,
        classification=classification,
        fire=fire_resp,
        flood=flood_resp,
        carcrash=carcrash_resp,
        objects=generic_resp,
    )


# ── Verdict logic ─────────────────────────────────────────────────────────


def _build_verdict(
    classification: ClassifyResponse,
    fire: FireResponse | None,
    flood: FloodResponse | None,
    carcrash: CarCrashResponse | None,
    generic: DetectResponse | None,
) -> Verdict:
    pred = classification.predicted_class
    conf = classification.confidence
    notes: list[str] = []

    # Low classifier confidence → uncertain headline (still surface details below).
    if conf < LOW_CONFIDENCE_THRESHOLD:
        notes.append(f"Low classifier confidence ({conf * 100:.1f}%). Inspect the detail panels below.")
        return Verdict(
            disaster_type="Uncertain",
            confidence=conf,
            primary_model="none",
            summary=f"Uncertain scene — best guess {pred} ({conf * 100:.0f}%).",
            annotated_image=generic.annotated_image if generic else None,
            notes=notes,
        )

    if pred == "Wildfire":
        if fire is None:
            notes.append("Fire detector unavailable — falling back to scene-level prediction only.")
            return _generic_only_verdict(classification, generic, notes)
        if fire.fire_count == 0 and fire.smoke_count == 0:
            notes.append("Classifier says Wildfire but the fire detector found no fire/smoke regions — downgrading.")
            return Verdict(
                disaster_type="Uncertain",
                confidence=conf,
                primary_model="none",
                summary="Wildfire predicted, but no flames/smoke detected.",
                annotated_image=fire.annotated_image,
                notes=notes,
            )
        return Verdict(
            disaster_type="Wildfire",
            confidence=conf,
            severity=fire.severity,
            affected_area_pct=fire.fire_area_pct,
            affected_area_m2=fire.estimated_area_m2,
            primary_model="fire",
            summary=_summary("Wildfire", fire.severity, fire.fire_area_pct, fire.estimated_area_m2,
                             extra=f"{fire.fire_count} fire / {fire.smoke_count} smoke region(s)"),
            annotated_image=fire.annotated_image,
            resources=fire.resources.model_dump(),
            notes=notes,
        )

    if pred == "Flood":
        if flood is None:
            notes.append("Flood segmenter unavailable — falling back to scene-level prediction.")
            return _generic_only_verdict(classification, generic, notes)
        if flood.flood_area_pct < 1.0:
            notes.append("Classifier says Flood but the segmenter found <1% inundated area — downgrading.")
            return Verdict(
                disaster_type="Uncertain",
                confidence=conf,
                primary_model="none",
                summary="Flood predicted, but no significant water mask detected.",
                annotated_image=flood.annotated_image,
                notes=notes,
            )
        return Verdict(
            disaster_type="Flood",
            confidence=conf,
            affected_area_pct=flood.flood_area_pct,
            affected_area_m2=flood.flood_area_m2,
            primary_model="flood",
            summary=_summary("Flood", None, flood.flood_area_pct, flood.flood_area_m2,
                             extra=f"{flood.buildings} buildings · {flood.vehicles} vehicles · {flood.people} people"),
            annotated_image=flood.annotated_image,
            notes=notes,
        )

    if pred == "Car Crash":
        if carcrash is None:
            notes.append("Car-crash detector unavailable — falling back to scene-level prediction.")
            return _generic_only_verdict(classification, generic, notes)
        if carcrash.accident_count == 0:
            notes.append("Classifier says Car Crash but the detector found no accident regions — downgrading.")
            return Verdict(
                disaster_type="Uncertain",
                confidence=conf,
                primary_model="none",
                summary="Car Crash predicted, but no accident boxes detected.",
                annotated_image=carcrash.annotated_image,
                notes=notes,
            )
        return Verdict(
            disaster_type="Car Crash",
            confidence=conf,
            severity=carcrash.severity,
            affected_area_pct=carcrash.accident_area_pct,
            affected_area_m2=carcrash.estimated_area_m2,
            primary_model="carcrash",
            summary=_summary("Car Crash", carcrash.severity, carcrash.accident_area_pct, carcrash.estimated_area_m2,
                             extra=f"{carcrash.accident_count} accident region(s)"),
            annotated_image=carcrash.annotated_image,
            resources=carcrash.resources.model_dump(),
            notes=notes,
        )

    # Cyclone / Earthquake → no specialist; rely on classifier + generic counts.
    if pred in ("Cyclone", "Earthquake"):
        return _generic_only_verdict(classification, generic, notes, headline=pred)

    # Unknown class — surface as-is.
    return _generic_only_verdict(classification, generic, notes, headline=pred)


def _generic_only_verdict(
    classification: ClassifyResponse,
    generic: DetectResponse | None,
    notes: list[str],
    headline: str | None = None,
) -> Verdict:
    label = headline or classification.predicted_class
    if generic is None:
        return Verdict(
            disaster_type=label,
            confidence=classification.confidence,
            primary_model="none",
            summary=f"{label} — no specialist detector available for this category.",
            notes=notes,
        )
    extras = []
    if generic.people:    extras.append(f"{generic.people} people")
    if generic.vehicles:  extras.append(f"{generic.vehicles} vehicles")
    if generic.buildings: extras.append(f"{generic.buildings} buildings")
    extras_str = " · ".join(extras) or "no notable objects"
    return Verdict(
        disaster_type=label,
        confidence=classification.confidence,
        affected_area_pct=generic.area_percent,
        affected_area_m2=generic.estimated_area_m2,
        primary_model="generic",
        summary=f"{label} — scene survey: {extras_str}.",
        annotated_image=generic.annotated_image,
        notes=notes,
    )


def _summary(label: str, severity: str | None, pct: float, m2: float, extra: str) -> str:
    parts = [label]
    if severity:
        parts.append(f"severity {severity}")
    parts.append(f"{pct:.1f}% of frame")
    if m2:
        parts.append(f"≈{m2:.0f} m²")
    parts.append(extra)
    return " — ".join(parts[:2]) + " · " + " · ".join(parts[2:])
