"""Shared fixtures.

The API is exercised without the trained weights (they are gitignored): every
model path points at a file that does not exist, so the registry reports the
models as unavailable and model-backed endpoints answer 503. The database is a
throwaway SQLite file, so no PostgreSQL server is needed to run the suite.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session", autouse=True)
def _isolated_settings(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("raid")
    missing = tmp / "missing-weights.pt"
    os.environ.update({
        "APP_DATABASE_URL": f"sqlite:///{tmp / 'test.db'}",
        "APP_IMAGE_DIR": str(tmp / "images"),
        "APP_OPENWEATHER_API_KEY": "",
        "APP_CLASSIFIER_WEIGHTS": str(missing),
        "APP_GENERIC_DETECTOR_WEIGHTS": str(missing),
        "APP_FLOOD_SEGMENTER_WEIGHTS": str(missing),
        "APP_FIRE_DETECTOR_WEIGHTS": str(missing),
        "APP_CARCRASH_DETECTOR_WEIGHTS": str(missing),
    })
    from app.config import get_settings
    get_settings.cache_clear()
    yield


@pytest.fixture(scope="session")
def client(_isolated_settings):
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c
