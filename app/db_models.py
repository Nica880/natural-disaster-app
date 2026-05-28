"""SQLAlchemy ORM models — the durable system of record.

Relationships:
    cameras   1───N  incidents
    cameras   1───N  analyses
    incidents 1───N  analyses        (an incident is an aggregate of frames)
    incidents 1───N  feedback

Every inference is an `Analysis` row (source = 'upload' | 'camera'). A camera
analysis that is event-worthy is linked to an `Incident` (analyses.incident_id).
Binary images live on the filesystem; only their references are stored here.

NB: annotations use `Optional[...]` rather than `X | None` because SQLAlchemy
resolves mapped annotations at runtime and the `|` union syntax isn't
evaluable on Python 3.9 (the project's local interpreter).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # natural key: 'cam-highway'
    label: Mapped[Optional[str]] = mapped_column(String)
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lon: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    incidents: Mapped[List["Incident"]] = relationship(back_populates="camera")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    camera_id: Mapped[Optional[str]] = mapped_column(ForeignKey("cameras.id"))
    disaster_type: Mapped[str] = mapped_column(String, index=True)
    severity: Mapped[Optional[str]] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text)
    peak_confidence: Mapped[float] = mapped_column(Float)
    affected_area_pct: Mapped[Optional[float]] = mapped_column(Float)
    affected_area_m2: Mapped[Optional[float]] = mapped_column(Float)
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lon: Mapped[Optional[float]] = mapped_column(Float)
    resources: Mapped[Optional[dict]] = mapped_column(JSONB)
    best_snapshot_path: Mapped[Optional[str]] = mapped_column(String)  # annotated frame on disk
    frame_count: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="active", index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    camera: Mapped[Optional["Camera"]] = relationship(back_populates="incidents")
    analyses: Mapped[List["Analysis"]] = relationship(back_populates="incident")
    feedback: Mapped[List["Feedback"]] = relationship(back_populates="incident")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String, index=True)  # 'upload' | 'camera'
    camera_id: Mapped[Optional[str]] = mapped_column(ForeignKey("cameras.id"))
    incident_id: Mapped[Optional[str]] = mapped_column(ForeignKey("incidents.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)

    # Verdict headline — typed for fast filtering / aggregation.
    disaster_type: Mapped[str] = mapped_column(String, index=True)
    confidence: Mapped[float] = mapped_column(Float)
    severity: Mapped[Optional[str]] = mapped_column(String)
    affected_area_pct: Mapped[Optional[float]] = mapped_column(Float)
    affected_area_m2: Mapped[Optional[float]] = mapped_column(Float)
    primary_model: Mapped[str] = mapped_column(String)

    # Full structured output (classification + per-model raw + resources).
    outputs: Mapped[Optional[dict]] = mapped_column(JSONB)

    original_image_path: Mapped[Optional[str]] = mapped_column(String)
    annotated_image_path: Mapped[Optional[str]] = mapped_column(String)

    incident: Mapped[Optional["Incident"]] = relationship(back_populates="analyses")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    verdict_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    actual_type: Mapped[Optional[str]] = mapped_column(String)  # ground truth when model was wrong
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    incident: Mapped["Incident"] = relationship(back_populates="feedback")
