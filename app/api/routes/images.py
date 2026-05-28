"""Serve persisted evidence frames by their storage reference.

Live SSE payloads embed snapshots as data-URIs, so this endpoint is for
history / analytics views that reference images by path instead.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services import storage

router = APIRouter(prefix="/api/v1", tags=["images"])


@router.get("/images/{ref:path}")
def get_image(ref: str) -> FileResponse:
    path = storage.resolve(ref)
    if not path.exists():
        raise HTTPException(404, "Image not found")
    return FileResponse(path, media_type="image/jpeg")
