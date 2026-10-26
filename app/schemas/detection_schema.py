"""
Esquemas Pydantic para listar y consultar detecciones guardadas.
"""

from datetime import datetime

from pydantic import BaseModel


class DetectionOut(BaseModel):
    id: int
    plant: str
    disease: str
    confidence: float
    image_path: str
    crop_id: int | None = None
    crop_name: str | None = None
    crop_variety: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DetectionListResponse(BaseModel):
    items: list[DetectionOut]
    total: int
