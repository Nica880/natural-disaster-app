"""Incident grouping: frames from the same camera and disaster class inside the
window collapse into one incident; dismissed threads stay silent."""
from __future__ import annotations

from app.schemas.responses import Verdict
from app.services.incidents import MAX_FRAMES_PER_INCIDENT, IncidentStore


def _verdict(kind: str = "Wildfire", conf: float = 0.8) -> Verdict:
    return Verdict(disaster_type=kind, confidence=conf, primary_model="fire", summary=f"{kind} detected")


def test_same_camera_and_class_are_grouped():
    store = IncidentStore()
    first = store.record("cam-1", "Ridge", None, None, _verdict(), None)
    second = store.record("cam-1", "Ridge", None, None, _verdict(), None)
    assert first is not None and second is not None
    assert first.id == second.id
    assert second.frame_count == 2
    assert len(store.list_active()) == 1


def test_different_class_or_camera_opens_new_incident():
    store = IncidentStore()
    a = store.record("cam-1", None, None, None, _verdict("Wildfire"), None)
    b = store.record("cam-1", None, None, None, _verdict("Flood"), None)
    c = store.record("cam-2", None, None, None, _verdict("Wildfire"), None)
    assert len({a.id, b.id, c.id}) == 3


def test_stronger_evidence_becomes_the_headline():
    store = IncidentStore()
    store.record("cam-1", None, None, None, _verdict(conf=0.6), None)
    inc = store.record("cam-1", None, None, None, _verdict(conf=0.95), "snap.jpg")
    assert inc.confidence == 0.95
    assert inc.snapshot == "snap.jpg"


def test_frames_are_capped():
    store = IncidentStore()
    for _ in range(MAX_FRAMES_PER_INCIDENT + 5):
        inc = store.record("cam-1", None, None, None, _verdict(), None)
    assert len(inc.frames) == MAX_FRAMES_PER_INCIDENT
    assert inc.frame_count == MAX_FRAMES_PER_INCIDENT + 5


def test_dismissed_incident_suppresses_new_frames():
    store = IncidentStore()
    inc = store.record("cam-1", None, None, None, _verdict(), None)
    assert store.dismiss(inc.id) is not None
    assert store.record("cam-1", None, None, None, _verdict(), None) is None
    assert store.list_active() == []


def test_dismiss_all_clears_the_board():
    store = IncidentStore()
    store.record("cam-1", None, None, None, _verdict("Wildfire"), None)
    store.record("cam-2", None, None, None, _verdict("Flood"), None)
    assert len(store.dismiss_all()) == 2
    assert store.list_active() == []
