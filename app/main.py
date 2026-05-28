"""FastAPI entry point. Run with:

    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_registry
from app.api.routes import analyze, classify, detect, drone, health, images, monitor
from app.config import get_settings
from app.db import init_db, session_scope
from app.logging import configure_logging
from app.services import repository
from app.services.incidents import get_incident_store

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)

    # Schema + rehydration: restore the live incident board from the durable
    # store so a restart doesn't drop active incidents.
    init_db()
    with session_scope() as session:
        active = repository.load_active_incidents(session)
    get_incident_store().load(active)

    log.info("Starting application — pre-loading models…")
    reg = get_registry()
    for m in reg.status():
        log.info("  %-10s loaded=%s  path=%s", m["name"], m["loaded"], m["path"])
    yield
    log.info("Application shutting down.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="RAID — Real-time Aerial Incident Detection API",
        description=(
            "Image analysis for drone-captured disaster scenes. "
            "Classification (ResNet18), generic object detection (YOLOv8 / OIV7), "
            "fire & smoke detection (YOLOv8 / D-Fire), flood segmentation (YOLOv8-seg)."
        ),
        version="0.2.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(analyze.router)
    app.include_router(classify.router)
    app.include_router(detect.router)
    app.include_router(drone.router)
    app.include_router(monitor.router)
    app.include_router(images.router)

    return app


app = create_app()
