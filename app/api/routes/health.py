from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import ModelRegistry, get_registry
from app.schemas.responses import HealthResponse, ModelStatus

router = APIRouter(tags=["health"])


@router.get("/", response_model=HealthResponse)
@router.get("/health", response_model=HealthResponse)
def health(reg: ModelRegistry = Depends(get_registry)) -> HealthResponse:
    return HealthResponse(models=[ModelStatus(**m) for m in reg.status()])
