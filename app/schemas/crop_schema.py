"""
Esquemas Pydantic para el módulo de "Mis cultivos".
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class CropCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    variety: str = Field(min_length=1, max_length=100)
    planting_date: date
    area_hectares: float | None = Field(default=None, ge=0)
    location_label: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    notes: str | None = None


class CropOut(BaseModel):
    id: int
    name: str
    variety: str
    planting_date: date
    area_hectares: float | None
    location_label: str | None
    latitude: float | None
    longitude: float | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CropListResponse(BaseModel):
    items: list[CropOut]
    total: int
