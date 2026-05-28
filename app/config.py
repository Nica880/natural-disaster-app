"""Application settings. Paths resolve relative to the repo root so the
server can be launched from any working directory.

Override any field at runtime via environment variables, e.g.:
    APP_CORS_ORIGINS='["https://foo.com"]' uvicorn app.main:app
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    # --- Server -----------------------------------------------------------
    cors_origins: list[str] = Field(default_factory=lambda: [
        "http://localhost:5173", "http://127.0.0.1:5173",   # main operator UI
        "http://localhost:5174", "http://127.0.0.1:5174",   # camera simulator
    ])
    log_level: str = "INFO"

    # --- Model artefact paths --------------------------------------------
    classifier_weights: Path = REPO_ROOT / "model" / "disaster_model.pth"
    generic_detector_weights: Path = REPO_ROOT / "yolov8n-oiv7.pt"
    flood_segmenter_weights: Path = REPO_ROOT / "model" / "flood.pt"
    fire_detector_weights: Path = REPO_ROOT / "model" / "fire.pt"
    carcrash_detector_weights: Path = REPO_ROOT / "model" / "carcrash.pt"

    # --- Inference defaults ----------------------------------------------
    detect_conf_threshold: float = 0.25
    detect_image_size: int = 640
    classify_image_size: int = 224

    # --- Persistence ------------------------------------------------------
    # Override via APP_DATABASE_URL / APP_IMAGE_DIR (e.g. in docker-compose).
    database_url: str = "postgresql+psycopg://raid:raid@localhost:5432/raid"
    image_dir: Path = REPO_ROOT / "data" / "images"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
