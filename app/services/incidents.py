"""In-memory incident store with SSE broadcast.

A detection from one camera is grouped with subsequent detections of the
same disaster class within INCIDENT_WINDOW_SECONDS — collapsing per-frame
noise into a single actionable incident. Subscribers receive create / update
/ dismiss events over Server-Sent Events.

The store is intentionally in-memory: the demo scope doesn't need persistence,
and a single-process FastAPI run is the deployment target. Swap for Redis +
pubsub if you ever need multi-worker.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator

from app.schemas.responses import Incident, IncidentFrame, Verdict

log = logging.getLogger(__name__)

INCIDENT_WINDOW_SECONDS = 60.0
SUBSCRIBER_QUEUE_MAX = 100
MAX_FRAMES_PER_INCIDENT = 8  # Keep recent evidence; cap to avoid memory bloat


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _seconds_since(iso: str) -> float:
    return (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds()


class IncidentStore:
    """Singleton incident store. Single-event-loop (uvicorn) means no locks
    are needed — every coroutine runs serially between awaits."""

    def __init__(self) -> None:
        self._incidents: dict[str, Incident] = {}
        self._subscribers: list[asyncio.Queue] = []

    # ── Detection intake ─────────────────────────────────────────────────

    def record(
        self,
        camera_id: str,
        location: str | None,
        lat: float | None,
        lon: float | None,
        verdict: Verdict,
        snapshot: str | None,
    ) -> Incident | None:
        """Group with a matching incident from the same camera + class within
        the window. Returns:
          - the active incident if grouped (live update)
          - the new incident if opened fresh
          - **None** if suppressed — a recently-dismissed incident in the same
            window means the operator already said "I've got this", so the
            frame is silently dropped (no event, no notification)."""
        now = _now_iso()
        frame = IncidentFrame(timestamp=now, confidence=verdict.confidence, snapshot=snapshot)

        existing = self._find_in_window(camera_id, verdict.disaster_type)

        # Operator already dismissed this thread — honour the silence.
        if existing is not None and existing.status == "dismissed":
            log.info(
                "[SUPPRESS] %s @ %s — dismissed incident %s still in cooldown (%.0fs ago)",
                verdict.disaster_type, camera_id, existing.id,
                _seconds_since(existing.last_seen),
            )
            return None

        if existing is not None:  # active match within window — group
            existing.last_seen = now
            existing.frame_count += 1
            existing.frames.append(frame)
            if len(existing.frames) > MAX_FRAMES_PER_INCIDENT:
                existing.frames = existing.frames[-MAX_FRAMES_PER_INCIDENT:]
            # Promote stronger evidence to the headline.
            if verdict.confidence > existing.confidence:
                existing.confidence         = verdict.confidence
                existing.snapshot           = snapshot
                existing.summary            = verdict.summary
                existing.severity           = verdict.severity
                existing.affected_area_pct  = verdict.affected_area_pct
                existing.affected_area_m2   = verdict.affected_area_m2
                existing.resources          = verdict.resources
            self._publish({"type": "update", "incident": existing.model_dump()})
            return existing

        incident = Incident(
            id=uuid.uuid4().hex[:12],
            camera_id=camera_id,
            location=location,
            lat=lat,
            lon=lon,
            disaster_type=verdict.disaster_type,
            severity=verdict.severity,
            confidence=verdict.confidence,
            affected_area_pct=verdict.affected_area_pct,
            affected_area_m2=verdict.affected_area_m2,
            first_seen=now,
            last_seen=now,
            frame_count=1,
            status="active",
            summary=verdict.summary,
            snapshot=snapshot,
            resources=verdict.resources,
            frames=[frame],
        )
        self._incidents[incident.id] = incident
        log.info("[INCIDENT %s] %s @ %s — %s", incident.id, incident.disaster_type, camera_id, incident.summary)
        self._publish({"type": "create", "incident": incident.model_dump()})
        return incident

    def get(self, incident_id: str) -> Incident | None:
        return self._incidents.get(incident_id)

    def load(self, incidents: list[Incident]) -> None:
        """Seed the store from persisted state (startup rehydration). Replaces
        the current set — call once before any subscribers connect."""
        self._incidents = {inc.id: inc for inc in incidents}
        if incidents:
            log.info("Rehydrated %d active incident(s) from store snapshot.", len(incidents))

    def list_active(self) -> list[Incident]:
        return sorted(
            (i for i in self._incidents.values() if i.status == "active"),
            key=lambda i: i.last_seen,
            reverse=True,
        )

    def dismiss(self, incident_id: str) -> Incident | None:
        inc = self._incidents.get(incident_id)
        if inc is None or inc.status == "dismissed":
            return None
        inc.status = "dismissed"
        self._publish({"type": "dismiss", "incident": inc.model_dump()})
        return inc

    # ── SSE pub/sub ──────────────────────────────────────────────────────

    async def subscribe(self) -> AsyncIterator[dict]:
        """Yields events for the lifetime of the connection. On connect, the
        current active set is replayed as `snapshot` events (distinct from
        live `create` events) so the UI can hydrate state without triggering
        per-incident alerts."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=SUBSCRIBER_QUEUE_MAX)
        self._subscribers.append(queue)
        try:
            for inc in self.list_active():
                await queue.put({"type": "snapshot", "incident": inc.model_dump()})
            while True:
                yield await queue.get()
        finally:
            self._subscribers.remove(queue)

    def _publish(self, event: dict) -> None:
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                log.warning("Subscriber queue full — dropping event %s", event.get("type"))

    # ── helpers ──────────────────────────────────────────────────────────

    def _find_in_window(self, camera_id: str, disaster_type: str) -> Incident | None:
        """Most-recent matching incident (any status) within the window."""
        best: Incident | None = None
        for inc in self._incidents.values():
            if inc.camera_id != camera_id or inc.disaster_type != disaster_type:
                continue
            if _seconds_since(inc.last_seen) >= INCIDENT_WINDOW_SECONDS:
                continue
            if best is None or inc.last_seen > best.last_seen:
                best = inc
        return best


_store: IncidentStore | None = None


def get_incident_store() -> IncidentStore:
    global _store
    if _store is None:
        _store = IncidentStore()
    return _store
