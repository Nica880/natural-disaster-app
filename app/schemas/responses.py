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


class FloodResources(BaseModel):
    boats: int
    ambulances: int
    evacuation_buses: int
    police_units: int
    smurd: int


class FloodResponse(BaseModel):
    flood_area_pct: float
    flood_area_m2: float
    severity: Literal["none", "minor", "moderate", "major", "catastrophic"] = "none"
    resources: FloodResources | None = None
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


# --- Live monitor (camera ingest + incidents) -----------------------------


class IncidentFrame(BaseModel):
    """One captured frame in an incident's evidence trail."""
    timestamp: str
    confidence: float
    snapshot: str | None = None


class Incident(BaseModel):
    """A grouped sequence of detections from one camera, one disaster class,
    within a short time window. Frame-by-frame noise collapses into a single
    actionable incident."""
    id: str
    camera_id: str
    location: str | None = None
    lat: float | None = None
    lon: float | None = None
    disaster_type: str
    severity: str | None = None
    confidence: float = Field(..., description="Peak classifier confidence across frames")
    affected_area_pct: float | None = None
    affected_area_m2: float | None = None
    first_seen: str
    last_seen: str
    frame_count: int
    status: Literal["active", "dismissed"] = "active"
    summary: str
    snapshot: str | None = Field(None, description="Best-evidence annotated frame, data URI JPEG")
    resources: dict | None = Field(None, description="Recommended units; shape varies by disaster type")
    frames: list[IncidentFrame] = Field(default_factory=list, description="Recent evidence frames (capped)")


class IngestResponse(BaseModel):
    """Ack returned to the camera. Cameras don't display analysis results —
    they only need to know the frame was accepted and whether it triggered."""
    accepted: bool = True
    triggered: bool = Field(..., description="True if the frame opened or updated an incident")
    incident_id: str | None = None


class IncidentSummary(BaseModel):
    """Lightweight incident row for the history list — no frames / no base64
    snapshot (just a storage ref the UI can turn into an image URL)."""
    id: str
    camera_id: str | None = None
    location: str | None = None
    disaster_type: str
    severity: str | None = None
    confidence: float
    frame_count: int
    status: str
    first_seen: str
    last_seen: str
    summary: str
    snapshot_ref: str | None = None


class DismissAllResponse(BaseModel):
    """Ack for the bulk dismiss. Deliberately just a count — returning the
    full incidents would ship their base64 frames for nothing; clients update
    from the per-incident SSE dismiss events instead."""
    dismissed: int = Field(..., description="Number of incidents dismissed")


class FeedbackCreate(BaseModel):
    """Operator ground-truth on an incident — powers real-world precision
    metrics and a re-training dataset."""
    verdict_correct: bool | None = Field(None, description="Was the detection correct?")
    actual_type: str | None = Field(None, description="True class if the model was wrong")
    notes: str | None = None


class FeedbackResponse(BaseModel):
    id: str
    incident_id: str
    verdict_correct: bool | None = None
    actual_type: str | None = None
    notes: str | None = None
    created_at: str


class FeedbackTypeStat(BaseModel):
    """Per-disaster-type precision from operator feedback."""
    disaster_type: str
    reviewed: int
    correct: int
    precision: float = Field(..., description="correct / reviewed, 0..1")


class FeedbackStats(BaseModel):
    """Aggregate detection-accuracy metrics computed from operator feedback."""
    total_reviewed: int
    total_correct: int
    total_false: int
    precision: float = Field(..., description="overall correct / reviewed, 0..1")
    by_type: list[FeedbackTypeStat]


# --- Weather (OpenWeather, per-incident location) --------------------------


class WeatherResponse(BaseModel):
    """Current conditions at an incident's coordinates, plus a disaster-aware
    risk note. The note turns raw weather into an operational signal — e.g. a
    wildfire under strong wind is escalated, a wildfire under heavy rain is
    de-escalated (see the dissertation's worked examples)."""
    description: str = Field(..., description="Human-readable sky condition, e.g. 'light rain'")
    icon: str | None = Field(None, description="OpenWeather icon code, e.g. '10d'")
    temp_c: float
    feels_like_c: float
    humidity_pct: int
    wind_speed_ms: float
    wind_speed_kmh: float
    wind_gust_ms: float | None = None
    wind_deg: int | None = None
    rain_1h_mm: float | None = Field(None, description="Rain volume, last hour (mm)")
    snow_1h_mm: float | None = Field(None, description="Snow volume, last hour (mm)")
    clouds_pct: int | None = None
    visibility_m: int | None = None
    observed_at: str = Field(..., description="ISO-8601 observation time (UTC)")
    place: str | None = Field(None, description="Nearest place name from OpenWeather")
    # Contextual risk — populated only when a disaster_type is supplied.
    risk_level: Literal["elevated", "normal", "reduced"] | None = None
    risk_note: str | None = Field(None, description="One-line operational implication of the weather")
