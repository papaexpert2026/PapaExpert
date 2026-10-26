"""
Acceso a datos de la tabla 'crops'.
"""

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.crop_model import Crop
from app.models.detection_model import Detection
from app.schemas.crop_schema import CropCreateRequest


class CropRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user_id: int, data: CropCreateRequest) -> Crop:
        crop = Crop(user_id=user_id, **data.model_dump())
        self.db.add(crop)
        self.db.commit()
        self.db.refresh(crop)
        return crop

    def get_by_id(self, crop_id: int, user_id: int) -> Crop | None:
        stmt = select(Crop).where(Crop.id == crop_id, Crop.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_user(self, user_id: int, limit: int = 50, offset: int = 0) -> tuple[list[Crop], int]:
        base_stmt = select(Crop).where(Crop.user_id == user_id).order_by(Crop.created_at.desc())
        items = list(self.db.execute(base_stmt.limit(limit).offset(offset)).scalars().all())

        count_stmt = select(func.count()).select_from(Crop).where(Crop.user_id == user_id)
        total = self.db.execute(count_stmt).scalar_one()

        return items, total

    def update(self, crop: Crop, data: CropCreateRequest) -> Crop:
        for field, value in data.model_dump().items():
            setattr(crop, field, value)
        self.db.commit()
        self.db.refresh(crop)
        return crop

    def delete(self, crop: Crop) -> None:
        self.db.delete(crop)
        self.db.commit()

    def get_detections_summary(self, crop_id: int, user_id: int) -> tuple[list[Detection], int, str | None]:
        """
        Retorna (detecciones_ordenadas_por_fecha_desc, total, nombre_de_la_ultima_enfermedad).
        Se filtra también por user_id para no exponer datos de otro usuario
        aunque alguien adivine un crop_id ajeno.
        """
        stmt = (
            select(Detection)
            .where(Detection.crop_id == crop_id, Detection.user_id == user_id)
            .order_by(Detection.created_at.desc(), Detection.id.desc())
        )
        items = list(self.db.execute(stmt).scalars().all())
        last_disease = items[0].disease if items else None
        return items, len(items), last_disease
