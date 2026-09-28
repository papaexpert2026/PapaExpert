"""
Esquemas Pydantic para las rutas de chat.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatSessionCreateRequest(BaseModel):
    detection_id: int


class ChatSessionOut(BaseModel):
    id: int
    detection_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSourceItem(BaseModel):
    title: str
    url: str


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: list[ChatSourceItem] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    session_id: int
    question: str = Field(min_length=1, max_length=2000)
    # Si es true, el asistente busca en internet además de usar el contexto
    # de la detección y el historial, y devuelve las fuentes consultadas.
    use_web_search: bool = False


class ChatResponseData(BaseModel):
    session_id: int
    answer: str
    message_id: int
    sources: list[ChatSourceItem] | None = None
