"""Image storage on the filesystem — content-addressed (SHA-256).

The DB stores only a relative reference (e.g. ``ab/abcd…ef.jpg``); the bytes
live under ``settings.image_dir`` on a Docker volume. Content addressing gives
free deduplication (identical frames collapse to one file).

This module is the single seam for blob storage: to move to S3 / MinIO later,
reimplement ``save_bytes`` / ``resolve`` / ``read_bytes`` and nothing else
changes.
"""
from __future__ import annotations

import base64
import hashlib
import io
from pathlib import Path

from PIL import Image

from app.config import get_settings


def _base() -> Path:
    d = get_settings().image_dir
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_bytes(data: bytes, ext: str = "jpg") -> str:
    """Persist bytes; return the relative reference to store in the DB."""
    digest = hashlib.sha256(data).hexdigest()
    ref = f"{digest[:2]}/{digest}.{ext}"
    path = _base() / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)
    return ref


def resolve(ref: str) -> Path:
    """Map a stored reference back to an absolute path (for serving)."""
    return _base() / ref


def read_bytes(ref: str) -> bytes | None:
    path = resolve(ref)
    return path.read_bytes() if path.exists() else None


# ── PIL / data-URI helpers ────────────────────────────────────────────────


def save_pil(image: Image.Image) -> str:
    """Re-encode a PIL image to JPEG and store it (used for originals)."""
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    return save_bytes(buf.getvalue(), "jpg")


def save_data_uri(data_uri: str | None) -> str | None:
    """Store the payload of a ``data:image/...;base64,...`` URI (annotated frames)."""
    if not data_uri or "," not in data_uri:
        return None
    _, b64 = data_uri.split(",", 1)
    return save_bytes(base64.b64decode(b64), "jpg")


def to_data_uri(ref: str | None) -> str | None:
    """Read a stored image back as a data URI (used on rehydration so the live
    SSE payload stays uniform — the frontend always gets a renderable src)."""
    if not ref:
        return None
    data = read_bytes(ref)
    if data is None:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()
