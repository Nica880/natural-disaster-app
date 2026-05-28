"""Singleton model instances + FastAPI dependency providers.

Models are heavy to load (especially YOLOs) so they're instantiated once
at startup and reused across requests. Each provider raises 503 if its
model failed to load (e.g. weights file missing).
"""
from __future__ import annotations

import io
import logging

from fastapi import Depends, File, HTTPException, UploadFile
from PIL import Image

from app.config import Settings, get_settings
from app.services.carcrash import CarCrashDetector
from app.services.classifier import DisasterClassifier
from app.services.detector import GenericDetector
from app.services.fire import FireDetector
from app.services.flood import FloodSegmenter

log = logging.getLogger(__name__)

# Longest-side cap for decoded uploads. YOLO resizes to its own imgsz (640)
# internally, so detection accuracy is unaffected — but this bounds the
# resolution that result.plot() draws mask overlays at. A dense segmentation
# (80+ FloodNet masks) on a multi-thousand-pixel UAV frame otherwise segfaults
# the native renderer.
MAX_IMAGE_SIDE = 1280


class ModelRegistry:
    """Lazy-loads each model on demand, caches results, swallows load errors
    so the app can boot even if one model's weights are missing.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._classifier: DisasterClassifier | None = None
        self._detector: GenericDetector | None = None
        self._flood: FloodSegmenter | None = None
        self._fire: FireDetector | None = None
        self._carcrash: CarCrashDetector | None = None
        self._errors: dict[str, str] = {}

    def _try(self, name: str, factory):
        try:
            return factory()
        except Exception as e:  # noqa: BLE001 — we *want* to log everything
            log.warning("Model '%s' unavailable: %s", name, e)
            self._errors[name] = str(e)
            return None

    def classifier(self) -> DisasterClassifier | None:
        if self._classifier is None and "classifier" not in self._errors:
            self._classifier = self._try(
                "classifier",
                lambda: DisasterClassifier(
                    self._settings.classifier_weights, image_size=self._settings.classify_image_size
                ),
            )
        return self._classifier

    def detector(self) -> GenericDetector | None:
        if self._detector is None and "detector" not in self._errors:
            self._detector = self._try(
                "detector",
                lambda: GenericDetector(
                    self._settings.generic_detector_weights,
                    image_size=self._settings.detect_image_size,
                    conf=self._settings.detect_conf_threshold,
                ),
            )
        return self._detector

    def flood(self) -> FloodSegmenter | None:
        if self._flood is None and "flood" not in self._errors:
            self._flood = self._try(
                "flood",
                lambda: FloodSegmenter(
                    self._settings.flood_segmenter_weights,
                    image_size=self._settings.detect_image_size,
                    conf=self._settings.detect_conf_threshold,
                ),
            )
        return self._flood

    def fire(self) -> FireDetector | None:
        if self._fire is None and "fire" not in self._errors:
            self._fire = self._try(
                "fire",
                lambda: FireDetector(
                    self._settings.fire_detector_weights,
                    image_size=self._settings.detect_image_size,
                    conf=self._settings.detect_conf_threshold,
                ),
            )
        return self._fire

    def carcrash(self) -> CarCrashDetector | None:
        if self._carcrash is None and "carcrash" not in self._errors:
            self._carcrash = self._try(
                "carcrash",
                lambda: CarCrashDetector(
                    self._settings.carcrash_detector_weights,
                    image_size=self._settings.detect_image_size,
                    conf=self._settings.detect_conf_threshold,
                ),
            )
        return self._carcrash

    def status(self) -> list[dict]:
        return [
            {"name": "classifier", "loaded": self.classifier() is not None, "path": str(self._settings.classifier_weights)},
            {"name": "detector",   "loaded": self.detector()   is not None, "path": str(self._settings.generic_detector_weights)},
            {"name": "flood",      "loaded": self.flood()      is not None, "path": str(self._settings.flood_segmenter_weights)},
            {"name": "fire",       "loaded": self.fire()       is not None, "path": str(self._settings.fire_detector_weights)},
            {"name": "carcrash",   "loaded": self.carcrash()   is not None, "path": str(self._settings.carcrash_detector_weights)},
        ]


_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry(get_settings())
    return _registry


# --- Dependency providers (each raises 503 if its model is unavailable) ----


def _require(model, name: str):
    if model is None:
        raise HTTPException(status_code=503, detail=f"{name} model not loaded — check server logs.")
    return model


def get_classifier(reg: ModelRegistry = Depends(get_registry)) -> DisasterClassifier:
    return _require(reg.classifier(), "Classifier")


def get_detector(reg: ModelRegistry = Depends(get_registry)) -> GenericDetector:
    return _require(reg.detector(), "Generic detector")


def get_flood(reg: ModelRegistry = Depends(get_registry)) -> FloodSegmenter:
    return _require(reg.flood(), "Flood segmenter")


def get_fire(reg: ModelRegistry = Depends(get_registry)) -> FireDetector:
    return _require(reg.fire(), "Fire detector")


def get_carcrash(reg: ModelRegistry = Depends(get_registry)) -> CarCrashDetector:
    return _require(reg.carcrash(), "Car-crash detector")


# --- Image upload helper ---------------------------------------------------


async def upload_image(file: UploadFile = File(...)) -> Image.Image:
    """Read an uploaded file and return a PIL Image. Raises 400 on bad input."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Expected an image, got {file.content_type}")
    data = await file.read()
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Could not decode image: {e}") from e
    if max(img.size) > MAX_IMAGE_SIDE:
        img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))  # in-place, keeps aspect ratio
    return img
