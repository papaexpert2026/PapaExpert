"""Procesa una imagen con YOLO sin guardar imágenes ni detecciones en SQL."""

import tempfile
from pathlib import Path

from fastapi import HTTPException, status

from app.config.disease_classes import get_disease_info
from app.schemas.prediction_schema import (
    BoundingBox,
    DetectionResultItem,
    PredictionResponseData,
)
from app.services.yolo_service import YOLOService


class TransientPredictionService:
    def run(self, contents: bytes, original_filename: str) -> PredictionResponseData:
        suffix = Path(original_filename).suffix.lower() or ".jpg"
        handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        image_path = Path(handle.name)
        try:
            with handle:
                handle.write(contents)

            try:
                yolo = YOLOService.get_instance()
            except FileNotFoundError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(exc),
                ) from exc

            try:
                raw_detections = yolo.predict(str(image_path))
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No se pudo analizar la imagen con el modelo de detección.",
                ) from exc

            items = []
            for raw in raw_detections:
                info = get_disease_info(raw.class_id)
                items.append(
                    DetectionResultItem(
                        class_id=raw.class_id,
                        class_name=info.class_name,
                        display_name=info.display_name,
                        confidence=round(raw.confidence, 4),
                        bbox=BoundingBox(
                            x1=raw.x1, y1=raw.y1, x2=raw.x2, y2=raw.y2
                        ),
                        description=info.description,
                        recommendation=info.recommendation,
                    )
                )

            return PredictionResponseData(
                detection_id=None,
                plant="papa",
                detections=items,
                image_url=None,
            )
        finally:
            image_path.unlink(missing_ok=True)
