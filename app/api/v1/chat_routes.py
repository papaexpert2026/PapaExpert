"""
POST /api/v1/chat/sessions
GET  /api/v1/chat/sessions/{id}
GET  /api/v1/chat/sessions/{id}/messages
POST /api/v1/chat
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user_model import User
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat_schema import (
    ChatMessageOut,
    ChatRequest,
    ChatSessionCreateRequest,
    ChatSessionOut,
)
from app.services.chat_service import ChatService
from app.utils.response_builder import success_response

router = APIRouter(tags=["Chat"])


@router.post("/chat/sessions")
def create_chat_session(
    payload: ChatSessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Request: { "detection_id": 12 }
    Response 200: sesión de chat creada, vinculada a esa detección.
    Errores: 404 si la detección no existe o no pertenece al usuario.
    """
    service = ChatService(db)
    session = service.create_session(user_id=current_user.id, detection_id=payload.detection_id)
    return success_response(
        data=ChatSessionOut.model_validate(session).model_dump(),
        message="Sesión de chat creada.",
    )


@router.get("/chat/sessions/{session_id}")
def get_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Response 200: info de la sesión. Errores: 404 si no existe."""
    repository = ChatRepository(db)
    session = repository.get_session(session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada.")

    return success_response(
        data=ChatSessionOut.model_validate(session).model_dump(),
        message="Sesión obtenida.",
    )


@router.get("/chat/sessions/{session_id}/messages")
def get_chat_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Response 200: historial completo de mensajes de la sesión, ordenados cronológicamente."""
    repository = ChatRepository(db)
    session = repository.get_session(session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada.")

    messages = repository.get_messages(session_id)
    return success_response(
        data=[ChatMessageOut.model_validate(m).model_dump() for m in messages],
        message="Mensajes obtenidos.",
    )


@router.post("/chat")
async def send_chat_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Request: { "session_id": 10, "question": "¿Cómo puedo controlar esta enfermedad?" }

    El backend recupera automáticamente la enfermedad, planta, confianza e
    historial asociados a la sesión — el usuario nunca necesita repetirlos.

    Response 200: { "session_id":..., "answer":..., "message_id":... }
    Errores: 404 si la sesión no existe, 503 si OpenAI no está disponible.
    """
    service = ChatService(db)
    result = await service.ask(
        user_id=current_user.id,
        session_id=payload.session_id,
        question=payload.question,
        use_web_search=payload.use_web_search,
    )
    return success_response(data=result.model_dump(), message="Respuesta generada.")
