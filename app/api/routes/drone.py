"""Drone upload endpoint — spec'd in Raport 3 (token auth + GPS metadata
+ webhook confirmation). Stubbed here; returns 501 until implemented.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile

from app.schemas.responses import DroneMetadata, DroneUploadResponse

router = APIRouter(prefix="/api/v1/drone", tags=["drone"])


@router.post("/upload", response_model=DroneUploadResponse, status_code=501)
async def upload(
    file: UploadFile = File(...),
    lat: float | None = Form(None),
    lon: float | None = Form(None),
    altitude_m: float | None = Form(None),
    captured_at: str | None = Form(None),
    authorization: str | None = Header(None),
):
    """Accepts an image + GPS metadata from a drone.

    NOT YET IMPLEMENTED — this endpoint is reserved per the Raport 3 spec.
    Once built it will: validate the bearer token, persist the file +
    metadata, kick off async analysis, and fire a webhook on completion.
    """
    raise HTTPException(
        status_code=501,
        detail="Drone upload endpoint not yet implemented. See docs/FIRE_TRAINING.md follow-ups.",
    )
