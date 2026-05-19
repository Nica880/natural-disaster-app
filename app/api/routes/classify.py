from __future__ import annotations

from fastapi import APIRouter, Depends
from PIL import Image

from app.api.deps import get_classifier, upload_image
from app.schemas.responses import ClassifyResponse
from app.services.classifier import DisasterClassifier

router = APIRouter(prefix="/api/v1", tags=["classify"])


@router.post("/classify", response_model=ClassifyResponse)
def classify(
    image: Image.Image = Depends(upload_image),
    model: DisasterClassifier = Depends(get_classifier),
) -> ClassifyResponse:
    """Classify a photo into one of: Car Crash, Cyclone, Earthquake, Flood, Wildfire."""
    return ClassifyResponse(**model.predict(image))
