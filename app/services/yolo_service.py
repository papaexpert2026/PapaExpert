"""
Servicio de inferencia YOLO.

Carga el modelo una sola vez (singleton) al iniciar el proceso, para no
recargar los pesos en cada request, y expone un método simple para
ejecutar la detección sobre una imagen.
"""

from dataclasses import dataclass
from pathlib import Path

from ultralytics import YOLO

from app.core.config import settings


@dataclass
class RawDetection:
    class_id: int
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class YOLOService:
    _instance: "YOLOService | None" = None

    def __init__(self) -> None:
        model_path = Path(settings.YOLO_MODEL_PATH)
        if not model_path.exists():
            raise FileNotFoundError(
                f"No se encontró el modelo YOLO en '{model_path}'. "
                "Coloca tu archivo best.pt en esa ruta (ver backend/models/README dentro del proyecto)."
            )
        self.model = YOLO(str(model_path))
        self.confidence_threshold = settings.YOLO_CONFIDENCE

    @classmethod
    def get_instance(cls) -> "YOLOService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, image_path: str) -> list[RawDetection]:
        """
        Ejecuta la inferencia sobre una imagen y retorna las detecciones
        que superan el umbral de confianza configurado.
        """
        results = self.model.predict(
            source=image_path,
            conf=self.confidence_threshold,
            verbose=False,
        )

        detections: list[RawDetection] = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                detections.append(
                    RawDetection(
                        class_id=class_id,
                        confidence=confidence,
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                    )
                )

        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections
