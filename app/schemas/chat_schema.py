"""
Esquemas Pydantic para las rutas de chat.
"""

from typing import Literal
from datetime import datetime

from pydantic import BaseModel, Field


class ChatSessionCreateRequest(BaseModel):
    # Opcional: si se omite o es null, se crea una sesión GENERAL (el
    # "Asistente IA" del menú, sin diagnóstico asociado).
    detection_id: int | None = None


class ChatSessionOut(BaseModel):
    id: int
    detection_id: int | None
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
    # de la detección (si la hay) y el historial, y devuelve las fuentes.
    use_web_search: bool = False


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatProcessRequest(BaseModel):
    """Entrada sin estado para generar respuestas; Firebase conserva el chat."""

    question: str = Field(min_length=1, max_length=2000)
    plant: str | None = Field(default=None, max_length=100)
    disease: str | None = Field(default=None, max_length=200)
    confidence: float | None = Field(default=None, ge=0, le=1)
    crop_name: str | None = Field(default=None, max_length=200)
    crop_variety: str | None = Field(default=None, max_length=200)
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=20)
    use_web_search: bool = False


class ChatProcessResponseData(BaseModel):
    answer: str
    sources: list[ChatSourceItem] | None = None


class ChatResponseData(BaseModel):
    session_id: int
    answer: str
    message_id: int
    sources: list[ChatSourceItem] | None = None
