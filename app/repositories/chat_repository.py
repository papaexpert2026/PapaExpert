"""
Acceso a datos de 'chat_sessions' y 'chat_messages'.
"""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat_session_model import ChatSession
from app.models.chat_message_model import ChatMessage


class ChatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_session(self, user_id: int, detection_id: int) -> ChatSession:
        session = ChatSession(user_id=user_id, detection_id=detection_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: int, user_id: int) -> ChatSession | None:
        stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_messages(self, session_id: int) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def add_message(
        self, session_id: int, role: str, content: str, sources: list[dict] | None = None
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            sources_json=json.dumps(sources) if sources else None,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
