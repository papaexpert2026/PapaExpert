"""
Esquemas Pydantic para el endpoint de predicción (YOLO).
"""

from pydantic import BaseModel


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionResultItem(BaseModel):
    class_id: int
    class_name: str
    display_name: str
    confidence: float
    bbox: BoundingBox
    description: str
    recommendation: str


class PredictionResponseData(BaseModel):
    detection_id: int | None = None
    plant: str
    detections: list[DetectionResultItem]
    image_url: str | None = None
