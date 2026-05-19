"""Render an Ultralytics inference result to a base64 JPEG data URI so the
frontend can show the annotated image without extra requests.

Ultralytics' `result.plot()` returns a BGR numpy array with boxes (and masks
when applicable) already drawn — we just encode it.
"""
from __future__ import annotations

import base64
import io
from typing import Any

import numpy as np
from PIL import Image as PILImage


def annotate_to_data_uri(result: Any, max_side: int = 960, quality: int = 80) -> str:
    """Return `data:image/jpeg;base64,…` for a YOLO result with overlays.

    Args:
      result: the first element of a `model.predict(...)` return.
      max_side: cap longest side so payload stays small (~50–200 KB).
      quality: JPEG quality (1–100).
    """
    arr_bgr = result.plot()  # numpy uint8, BGR
    arr_rgb = np.ascontiguousarray(arr_bgr[:, :, ::-1])
    img = PILImage.fromarray(arr_rgb)

    # Down-scale very large frames so the response stays small.
    if max(img.size) > max_side:
        ratio = max_side / max(img.size)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), PILImage.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"
