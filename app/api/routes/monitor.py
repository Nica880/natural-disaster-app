"""Live monitor — camera frame ingest + SSE incident feed + feedback.

Cameras POST frames to ``/ingest``. The same unified analyze pipeline runs
server-side; if the verdict is event-worthy, the detection is grouped into
an incident (in-memory, for instant SSE) and written through to Postgres
(durable system of record). Operators submit ground-truth via ``/feedback``.

Grouping logic lives in :mod:`app.services.incidents`, detection in
:mod:`app.api.routes.analyze`, persistence in :mod:`app.services.repository`.
This file is glue.
"""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image
from sqlalchemy.orm import Session

from app.api.deps import ModelRegistry, get_registry, upload_image
from app.api.routes.analyze import analyze
from app.db import get_db
from app.schemas.responses import (
    FeedbackCreate,
    FeedbackResponse,
    Incident,
    IncidentSummary,
    IngestResponse,
)
from app.services import repository
from app.services.incidents import IncidentStore, get_incident_store

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["monitor"])

# Verdicts outside this set are considered "no event" (Uncertain / unknown).
EVENT_WORTHY_TYPES = {"Wildfire", "Flood", "Car Crash", "Cyclone", "Earthquake"}


@router.post("/ingest", response_model=IngestResponse)
def ingest(
    camera_id: str = Form(...),
    location: str | None = Form(None),
    lat: float | None = Form(None),
    lon: float | None = Form(None),
    image: Image.Image = Depends(upload_image),
    reg: ModelRegistry = Depends(get_registry),
    store: IncidentStore = Depends(get_incident_store),
    db: Session = Depends(get_db),
) -> IngestResponse:
    """Cameras stream frames here. Returns a tiny ack — no analysis payload."""
    result = analyze(image=image, reg=reg)
    verdict = result.verdict

    if verdict.disaster_type not in EVENT_WORTHY_TYPES:
        return IngestResponse(triggered=False)

    incident = store.record(camera_id, location, lat, lon, verdict, verdict.annotated_image)
    # `record()` returns None when the operator has dismissed a matching
    # incident in the same window — honour the silence, ack with no event.
    if incident is None:
        return IngestResponse(triggered=False)

    # Write-through to the durable store: camera heartbeat, incident upsert,
    # and the frame itself as an analysis row linked to the incident.
    repository.upsert_camera(db, camera_id, location, lat, lon)
    repository.upsert_incident(db, incident)
    repository.persist_analysis(
        db, source="camera", camera_id=camera_id, incident_id=incident.id,
        result=result, original_image=image,
    )
    db.commit()
    return IngestResponse(triggered=True, incident_id=incident.id)


@router.get("/incidents", response_model=list[Incident])
def list_incidents(store: IncidentStore = Depends(get_incident_store)) -> list[Incident]:
    """Snapshot of currently active incidents. UI uses the SSE stream instead;
    this exists for tooling / debugging."""
    return store.list_active()


# NOTE: `/incidents/stream` MUST be declared before `/incidents/{incident_id}`
# — FastAPI matches routes in declaration order, and the path parameter
# would otherwise swallow "stream" as an incident id.
@router.get("/incidents/stream")
async def stream_incidents(
    store: IncidentStore = Depends(get_incident_store),
) -> StreamingResponse:
    """Server-Sent Events: pushes create / update / dismiss events as they
    happen. On connect, the current active set is replayed so the UI can
    render without an extra REST round-trip."""
    async def event_stream():
        try:
            async for event in store.subscribe():
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Declared before `/incidents/{incident_id}` for the same reason as `/stream`.
@router.get("/incidents/history", response_model=list[IncidentSummary])
def incident_history(
    limit: int = 50, db: Session = Depends(get_db)
) -> list[IncidentSummary]:
    """Closed (dismissed/resolved) incidents, most recent first — powers the
    history dropdown. Light payload (no frames / base64)."""
    return repository.list_incident_history(db, limit=min(limit, 200))


@router.get("/incidents/{incident_id}", response_model=Incident)
def get_incident(
    incident_id: str,
    store: IncidentStore = Depends(get_incident_store),
    db: Session = Depends(get_db),
) -> Incident:
    """Single-incident fetch. Active incidents come from the in-memory store;
    closed ones fall back to the durable store (used by the history modal)."""
    inc = store.get(incident_id) or repository.load_incident(db, incident_id)
    if inc is None:
        raise HTTPException(404, "Incident not found")
    return inc


@router.post("/incidents/{incident_id}/dismiss", response_model=Incident)
def dismiss_incident(
    incident_id: str,
    store: IncidentStore = Depends(get_incident_store),
    db: Session = Depends(get_db),
) -> Incident:
    inc = store.dismiss(incident_id)
    if inc is None:
        raise HTTPException(404, "Incident not found")
    repository.mark_dismissed(db, incident_id)
    db.commit()
    return inc


@router.post("/incidents/{incident_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    incident_id: str,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    """Operator ground-truth: was this detection correct? Feeds precision
    metrics and a re-training dataset."""
    if not repository.incident_exists(db, incident_id):
        raise HTTPException(404, "Incident not found")
    fb = repository.add_feedback(db, incident_id, payload.verdict_correct, payload.actual_type, payload.notes)
    db.commit()
    return FeedbackResponse(
        id=fb.id, incident_id=fb.incident_id, verdict_correct=fb.verdict_correct,
        actual_type=fb.actual_type, notes=fb.notes,
        created_at=fb.created_at.isoformat(timespec="seconds"),
    )
