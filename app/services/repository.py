"""Persistence layer — maps between the in-memory Pydantic `Incident`
(used by the live store + SSE) and the durable SQLAlchemy rows.

Kept as plain functions taking an explicit `Session` so the call sites
(route handlers, startup rehydration) control the transaction boundary.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app import db_models as m
from app.schemas.responses import (
    AnalyzeResponse,
    FeedbackStats,
    FeedbackTypeStat,
    Incident,
    IncidentFrame,
    IncidentSummary,
)
from app.services import storage

log = logging.getLogger(__name__)


# ── Cameras ────────────────────────────────────────────────────────────────


def upsert_camera(session: Session, camera_id: str, label: str | None, lat: float | None, lon: float | None) -> None:
    """Auto-register a camera on first sight; refresh its heartbeat otherwise."""
    cam = session.get(m.Camera, camera_id)
    now = datetime.now(timezone.utc)
    if cam is None:
        session.add(m.Camera(id=camera_id, label=label, lat=lat, lon=lon, last_seen_at=now))
    else:
        cam.last_seen_at = now
        if label is not None:
            cam.label = label
        if lat is not None:
            cam.lat = lat
        if lon is not None:
            cam.lon = lon


# ── Analyses (inference log) ────────────────────────────────────────────────


def persist_analysis(
    session: Session,
    *,
    source: str,
    camera_id: str | None,
    incident_id: str | None,
    result: AnalyzeResponse,
    original_image: Image.Image | None,
) -> str:
    """Store one inference. Images go to the blob store; only refs land here.
    The full per-model output is stored as JSONB with the heavy annotated
    data-URIs stripped (those live on disk)."""
    verdict = result.verdict
    original_ref = storage.save_pil(original_image) if original_image is not None else None
    annotated_ref = storage.save_data_uri(verdict.annotated_image)

    row = m.Analysis(
        source=source,
        camera_id=camera_id,
        incident_id=incident_id,
        disaster_type=verdict.disaster_type,
        confidence=verdict.confidence,
        severity=verdict.severity,
        affected_area_pct=verdict.affected_area_pct,
        affected_area_m2=verdict.affected_area_m2,
        primary_model=verdict.primary_model,
        outputs=_strip_images(result.model_dump()),
        original_image_path=original_ref,
        annotated_image_path=annotated_ref,
    )
    session.add(row)
    session.flush()
    return row.id


# ── Incidents (write-through from the in-memory store) ──────────────────────


def upsert_incident(session: Session, inc: Incident) -> None:
    """Insert-or-update the durable incident row from its in-memory form.
    The snapshot data-URI is saved to the blob store (idempotent — content
    addressing means a repeated save is a no-op) and only the ref is stored."""
    best_ref = storage.save_data_uri(inc.snapshot)
    fields = dict(
        camera_id=inc.camera_id,
        disaster_type=inc.disaster_type,
        severity=inc.severity,
        summary=inc.summary,
        peak_confidence=inc.confidence,
        affected_area_pct=inc.affected_area_pct,
        affected_area_m2=inc.affected_area_m2,
        lat=inc.lat,
        lon=inc.lon,
        resources=inc.resources,
        best_snapshot_path=best_ref,
        frame_count=inc.frame_count,
        status=inc.status,
        first_seen_at=datetime.fromisoformat(inc.first_seen),
        last_seen_at=datetime.fromisoformat(inc.last_seen),
    )
    row = session.get(m.Incident, inc.id)
    if row is None:
        session.add(m.Incident(id=inc.id, **fields))
    else:
        for key, val in fields.items():
            setattr(row, key, val)


def mark_dismissed(session: Session, incident_id: str) -> None:
    row = session.get(m.Incident, incident_id)
    if row is not None:
        row.status = "dismissed"
        row.dismissed_at = datetime.now(timezone.utc)


def _to_incident(session: Session, r: m.Incident) -> Incident:
    """Full reconstruction (frames + data-URI snapshots) of one incident row.
    Heavy (reads + base64-encodes images) — use for single incidents or the
    small active set, not bulk history."""
    frame_rows = session.scalars(
        select(m.Analysis).where(m.Analysis.incident_id == r.id).order_by(m.Analysis.created_at)
    ).all()
    frames = [
        IncidentFrame(
            timestamp=a.created_at.isoformat(timespec="seconds"),
            confidence=a.confidence,
            snapshot=storage.to_data_uri(a.annotated_image_path),
        )
        for a in frame_rows
    ]
    return Incident(
        id=r.id,
        camera_id=r.camera_id,
        location=r.camera.label if r.camera else None,
        lat=r.lat,
        lon=r.lon,
        disaster_type=r.disaster_type,
        severity=r.severity,
        confidence=r.peak_confidence,
        affected_area_pct=r.affected_area_pct,
        affected_area_m2=r.affected_area_m2,
        first_seen=r.first_seen_at.isoformat(timespec="seconds"),
        last_seen=r.last_seen_at.isoformat(timespec="seconds"),
        frame_count=r.frame_count,
        status=r.status,
        summary=r.summary,
        snapshot=storage.to_data_uri(r.best_snapshot_path),
        resources=r.resources,
        frames=frames,
    )


def load_active_incidents(session: Session) -> list[Incident]:
    """Rebuild the in-memory incidents for the active set — called at startup
    so a restart doesn't lose the live board."""
    rows = session.scalars(select(m.Incident).where(m.Incident.status == "active")).all()
    return [_to_incident(session, r) for r in rows]


def load_incident(session: Session, incident_id: str) -> Incident | None:
    """Full single incident of any status — used when opening a history item
    in the detail modal (the in-memory store only holds active ones)."""
    r = session.get(m.Incident, incident_id)
    return _to_incident(session, r) if r is not None else None


def list_incident_history(session: Session, limit: int = 50) -> list[IncidentSummary]:
    """Light, recent-first list of closed (non-active) incidents for the
    history dropdown — metadata only, no frames / base64."""
    rows = session.scalars(
        select(m.Incident)
        .where(m.Incident.status != "active")
        .options(joinedload(m.Incident.camera))
        .order_by(m.Incident.last_seen_at.desc())
        .limit(limit)
    ).all()
    return [
        IncidentSummary(
            id=r.id,
            camera_id=r.camera_id,
            location=r.camera.label if r.camera else None,
            disaster_type=r.disaster_type,
            severity=r.severity,
            confidence=r.peak_confidence,
            frame_count=r.frame_count,
            status=r.status,
            first_seen=r.first_seen_at.isoformat(timespec="seconds"),
            last_seen=r.last_seen_at.isoformat(timespec="seconds"),
            summary=r.summary,
            snapshot_ref=r.best_snapshot_path,
        )
        for r in rows
    ]


# ── Feedback ────────────────────────────────────────────────────────────────


def add_feedback(
    session: Session,
    incident_id: str,
    verdict_correct: bool | None,
    actual_type: str | None,
    notes: str | None,
) -> m.Feedback:
    fb = m.Feedback(
        incident_id=incident_id,
        verdict_correct=verdict_correct,
        actual_type=actual_type,
        notes=notes,
    )
    session.add(fb)
    session.flush()
    return fb


def incident_exists(session: Session, incident_id: str) -> bool:
    return session.get(m.Incident, incident_id) is not None


def feedback_stats(session: Session) -> FeedbackStats:
    """Detection-accuracy metrics from the feedback table, joined to incidents
    and grouped by disaster type. `correct` counts only rows where the operator
    marked the verdict correct (verdict_correct True); False or NULL count as
    not-correct. Precision guards divide-by-zero → 0.0."""
    rows = session.execute(
        select(
            m.Incident.disaster_type,
            func.count(m.Feedback.id),
            func.count(m.Feedback.id).filter(m.Feedback.verdict_correct.is_(True)),
        )
        .join(m.Incident, m.Feedback.incident_id == m.Incident.id)
        .group_by(m.Incident.disaster_type)
    ).all()

    by_type: list[FeedbackTypeStat] = []
    total_reviewed = 0
    total_correct = 0
    for disaster_type, reviewed, correct in rows:
        total_reviewed += reviewed
        total_correct += correct
        by_type.append(
            FeedbackTypeStat(
                disaster_type=disaster_type,
                reviewed=reviewed,
                correct=correct,
                precision=(correct / reviewed) if reviewed else 0.0,
            )
        )

    by_type.sort(key=lambda s: s.reviewed, reverse=True)
    return FeedbackStats(
        total_reviewed=total_reviewed,
        total_correct=total_correct,
        total_false=total_reviewed - total_correct,
        precision=(total_correct / total_reviewed) if total_reviewed else 0.0,
        by_type=by_type,
    )


# ── helpers ─────────────────────────────────────────────────────────────────


def _strip_images(obj):
    """Recursively null out `annotated_image` keys — they're large data-URIs
    already persisted to the blob store, so we don't duplicate them in JSONB."""
    if isinstance(obj, dict):
        return {k: (None if k == "annotated_image" else _strip_images(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_images(v) for v in obj]
    return obj
