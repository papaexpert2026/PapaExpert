"""
Orquesta el flujo completo de una predicción:
validar imagen -> guardar en disco -> ejecutar YOLO -> mapear clases -> guardar detección.
"""

import uuid
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.disease_classes import get_disease_info
from app.core.paths import UPLOADS_DIR
from app.repositories.detection_repository import DetectionRepository
from app.schemas.prediction_schema import BoundingBox, DetectionResultItem, PredictionResponseData
from app.services.yolo_service import YOLOService


class PredictionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.detection_repository = DetectionRepository(db)

    def _save_image(self, contents: bytes, original_filename: str) -> Path:
        upload_dir = UPLOADS_DIR

        extension = Path(original_filename).suffix.lower() or ".jpg"
        unique_name = f"{uuid.uuid4().hex}{extension}"
        destination = upload_dir / unique_name

        with open(destination, "wb") as f:
            f.write(contents)

        return destination

    def run_prediction(
        self,
        user_id: int,
        contents: bytes,
        original_filename: str,
        crop_id: int | None = None,
    ) -> PredictionResponseData:
        image_path = self._save_image(contents, original_filename)

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

        if not raw_detections:
            return PredictionResponseData(
                plant="papa",
                detections=[],
                image_url=str(image_path),
                crop_id=crop_id,
            )

        result_items: list[DetectionResultItem] = []
        for raw in raw_detections:
            info = get_disease_info(raw.class_id)
            result_items.append(
                DetectionResultItem(
                    class_id=raw.class_id,
                    class_name=info.class_name,
                    display_name=info.display_name,
                    confidence=round(raw.confidence, 4),
                    bbox=BoundingBox(x1=raw.x1, y1=raw.y1, x2=raw.x2, y2=raw.y2),
                    description=info.description,
                    recommendation=info.recommendation,
                )
            )

        top_result = result_items[0]

        detection = self.detection_repository.create(
            user_id=user_id,
            plant="papa",
            disease=top_result.display_name,
            confidence=top_result.confidence,
            image_path=str(image_path),
            crop_id=crop_id,
        )

        return PredictionResponseData(
            detection_id=detection.id,
            plant="papa",
            detections=result_items,
            image_url=str(image_path),
            crop_id=detection.crop_id,
            crop_name=detection.crop_name,
            crop_variety=detection.crop_variety,
        )
