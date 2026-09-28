"""
Orquesta el flujo completo de una predicción:
validar imagen -> guardar en disco -> ejecutar YOLO -> mapear clases -> guardar detección.
"""

import uuid
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.disease_classes import get_disease_info
from app.core.paths import UPLOADS_DIR  # <-- CAMBIO: misma fuente que main.py
from app.repositories.detection_repository import DetectionRepository
from app.schemas.prediction_schema import BoundingBox, DetectionResultItem, PredictionResponseData
from app.services.yolo_service import YOLOService


class PredictionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.detection_repository = DetectionRepository(db)

    def _save_image(self, contents: bytes, original_filename: str) -> tuple[Path, str]:
        """
        Guarda la imagen en la carpeta de uploads y devuelve:
        - destination: la ruta absoluta real en disco (para que YOLO pueda
          abrir el archivo).
        - relative_url_path: la ruta relativa y LIMPIA (siempre con '/',
          nunca con '\\', sin importar el sistema operativo) que se guarda
          en la base de datos y que Flutter usa para armar la URL completa.
        """
        extension = Path(original_filename).suffix.lower() or ".jpg"
        unique_name = f"{uuid.uuid4().hex}{extension}"
        destination = UPLOADS_DIR / unique_name

        with open(destination, "wb") as f:
            f.write(contents)

        # .as_posix() fuerza '/' siempre, incluso en Windows. Esto es clave:
        # antes se guardaba str(destination), que en Windows produce
        # backslashes ('uploads\\archivo.jpg'), rompiendo la URL que arma
        # la app Flutter.
        relative_url_path = f"uploads/{unique_name}"

        return destination, relative_url_path

    def run_prediction(self, user_id: int, contents: bytes, original_filename: str) -> PredictionResponseData:
        image_path, image_url_path = self._save_image(contents, original_filename)

        try:
            yolo = YOLOService.get_instance()
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        try:
            # YOLO sigue recibiendo la ruta ABSOLUTA real (image_path),
            # eso no cambia: necesita poder abrir el archivo físicamente.
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
                image_url=image_url_path,
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

        # CAMBIO CLAVE: se guarda image_url_path (relativo, limpio, ej.
        # "uploads/abc123.jpg"), NO la ruta absoluta del disco. Esa ruta
        # relativa es justo lo que tu app Flutter espera para armar
        # http://<host>/uploads/abc123.jpg con resolveBackendImageUrl().
        detection = self.detection_repository.create(
            user_id=user_id,
            plant="papa",
            disease=top_result.display_name,
            confidence=top_result.confidence,
            image_path=image_url_path,
        )

        return PredictionResponseData(
            detection_id=detection.id,
            plant="papa",
            detections=result_items,
            image_url=image_url_path,
        )