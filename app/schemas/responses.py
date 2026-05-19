"""Pydantic response schemas — typed I/O and free OpenAPI docs at /docs."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# --- Health ----------------------------------------------------------------


class ModelStatus(BaseModel):
    name: str
    loaded: bool
    path: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    models: list[ModelStatus]


# --- Classification --------------------------------------------------------


class ClassifyResponse(BaseModel):
    predicted_class: str
    confidence: float
    probabilities: dict[str, float]


# --- Generic object detection ---------------------------------------------


class DetectResponse(BaseModel):
    vehicles: int
    people: int
    buildings: int
    area_percent: float = Field(..., description="Sum of bbox areas / image area * 100")
    estimated_area_m2: float = Field(..., description="Sum of per-class real-world priors")
    objects_detected: int
    class_counts: dict[str, int]
    annotated_image: str | None = Field(None, description="Data URI JPEG with boxes drawn")


# --- Fire-specific ---------------------------------------------------------


class FireDetection(BaseModel):
    cls: str = Field(..., alias="class")
    confidence: float
    bbox: list[float]

    model_config = {"populate_by_name": True}


class ResourceRecommendation(BaseModel):
    fire_trucks: int
    ambulances: int
    police_units: int
    aerial_units: int
    smurd: int


class FireResponse(BaseModel):
    fire_count: int
    smoke_count: int
    fire_area_pct: float
    smoke_area_pct: float
    severity: Literal["none", "small", "medium", "large", "extreme"]
    estimated_area_m2: float
    resources: ResourceRecommendation
    detections: list[FireDetection]
    annotated_image: str | None = None


# --- Car-crash-specific ----------------------------------------------------


class CarCrashDetection(BaseModel):
    cls: str = Field(..., alias="class")
    confidence: float
    bbox: list[float]

    model_config = {"populate_by_name": True}


class CarCrashResourceRecommendation(BaseModel):
    ambulances: int
    police_units: int
    fire_trucks: int
    smurd: int
    tow_trucks: int


class CarCrashResponse(BaseModel):
    accident_count: int
    accident_area_pct: float
    estimated_area_m2: float
    severity: Literal["none", "minor", "moderate", "major"]
    resources: CarCrashResourceRecommendation
    detections: list[CarCrashDetection]
    annotated_image: str | None = None


# --- Flood-specific --------------------------------------------------------


class FloodResponse(BaseModel):
    flood_area_pct: float
    flood_area_m2: float
    buildings: int
    vehicles: int
    people: int
    plants: int
    total_objects: int
    class_counts: dict[str, int] = Field(default_factory=dict)
    annotated_image: str | None = None


# --- Unified auto-analysis -------------------------------------------------


class Verdict(BaseModel):
    """The headline answer the operator sees. Driven by the scene classifier
    but cross-checked with the matching specialist detector when available."""
    disaster_type: str = Field(..., description="Scene class: Wildfire / Flood / Cyclone / Earthquake / Car Crash / Uncertain")
    confidence: float = Field(..., description="Classifier confidence (0-1)")
    severity: str | None = Field(None, description="Specialist severity tier when applicable")
    affected_area_pct: float | None = None
    affected_area_m2: float | None = None
    primary_model: Literal["fire", "flood", "carcrash", "generic", "none"]
    summary: str = Field(..., description="One-line human-readable headline")
    annotated_image: str | None = None
    resources: dict | None = None
    notes: list[str] = Field(default_factory=list, description="Caveats / disagreements")


class AnalyzeResponse(BaseModel):
    verdict: Verdict
    classification: ClassifyResponse
    fire: FireResponse | None = None
    flood: FloodResponse | None = None
    carcrash: CarCrashResponse | None = None
    objects: DetectResponse | None = None


# --- Drone upload (stub) ---------------------------------------------------


class DroneMetadata(BaseModel):
    lat: float | None = None
    lon: float | None = None
    altitude_m: float | None = None
    captured_at: str | None = None


class DroneUploadResponse(BaseModel):
    accepted: bool
    upload_id: str
    metadata: DroneMetadata
