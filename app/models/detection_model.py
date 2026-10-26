"""
Modelo de detección: resultado de una inferencia YOLO guardado en la base de datos.
"""

from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Nullable a propósito: los diagnósticos ya existentes (hechos antes de
    # este cambio) no tenían cultivo asociado y deben seguir funcionando.
    crop_id: Mapped[int | None] = mapped_column(ForeignKey("crops.id"), nullable=True, index=True)

    plant: Mapped[str] = mapped_column(String(100), nullable=False)
    disease: Mapped[str] = mapped_column(String(150), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="detections")
    crop = relationship("Crop", back_populates="detections")
    chat_sessions = relationship("ChatSession", back_populates="detection", cascade="all, delete-orphan")

    @property
    def crop_name(self) -> str | None:
        return self.crop.name if self.crop is not None else None

    @property
    def crop_variety(self) -> str | None:
        return self.crop.variety if self.crop is not None else None
