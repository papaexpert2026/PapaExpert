"""
Acceso a datos de la tabla 'detections'.
"""

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.detection_model import Detection


class DetectionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user_id: int, plant: str, disease: str, confidence: float, image_path: str) -> Detection:
        detection = Detection(
            user_id=user_id,
            plant=plant,
            disease=disease,
            confidence=confidence,
            image_path=image_path,
        )
        self.db.add(detection)
        self.db.commit()
        self.db.refresh(detection)
        return detection

    def get_by_id(self, detection_id: int, user_id: int) -> Detection | None:
        stmt = select(Detection).where(Detection.id == detection_id, Detection.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_user(self, user_id: int, limit: int = 50, offset: int = 0) -> tuple[list[Detection], int]:
        base_stmt = select(Detection).where(Detection.user_id == user_id).order_by(Detection.created_at.desc())
        items = list(self.db.execute(base_stmt.limit(limit).offset(offset)).scalars().all())

        count_stmt = select(func.count()).select_from(Detection).where(Detection.user_id == user_id)
        total = self.db.execute(count_stmt).scalar_one()

        return items, total
