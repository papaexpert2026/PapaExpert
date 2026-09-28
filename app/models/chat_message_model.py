"""
Modelo de mensaje individual dentro de una sesión de chat.
"""

from datetime import datetime
import json

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), nullable=False, index=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # JSON con [{"title": "...", "url": "..."}, ...] cuando la respuesta vino
    # de una búsqueda web; NULL cuando es una respuesta normal sin fuentes.
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")

    @property
    def sources(self) -> list[dict] | None:
        """Decodifica sources_json a una lista de dicts para los esquemas Pydantic."""
        if not self.sources_json:
            return None
        try:
            return json.loads(self.sources_json)
        except (ValueError, TypeError):
            return None
