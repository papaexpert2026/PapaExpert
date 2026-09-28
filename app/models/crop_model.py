"""
Modelo de cultivo: un cultivo de papa que el usuario registra y administra.
"""

from datetime import date, datetime

from sqlalchemy import String, Float, Date, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    variety: Mapped[str] = mapped_column(String(100), nullable=False)
    planting_date: Mapped[date] = mapped_column(Date, nullable=False)
    area_hectares: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Ubicación del cultivo: texto legible + coordenadas opcionales
    # (no se exigen coordenadas exactas, ver disease_classes-style docstring
    # en el modelo de detección para el mismo criterio de no forzar datos).
    location_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
