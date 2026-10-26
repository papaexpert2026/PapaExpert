"""
Orquesta el flujo de chat:
recuperar detección (si la hay) -> recuperar historial -> consultar OpenAI -> guardar mensaje.

Una sesión con detection_id = None es una conversación GENERAL del asistente
(el "Asistente IA" accesible desde el menú), sin partir de un diagnóstico
concreto: el usuario puede preguntar por cualquier enfermedad que la app conozca.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.chat_repository import ChatRepository
from app.repositories.detection_repository import DetectionRepository
from app.schemas.chat_schema import ChatResponseData, ChatSourceItem
from app.services.openai_service import ask_assistant, ask_assistant_with_web_search, OpenAIServiceError


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.chat_repository = ChatRepository(db)
        self.detection_repository = DetectionRepository(db)

    def create_session(self, user_id: int, detection_id: int | None):
        if detection_id is not None:
            detection = self.detection_repository.get_by_id(detection_id, user_id)
            if detection is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No se encontró la detección indicada.",
                )
        # Si detection_id es None, se crea una sesión general sin validar nada más.
        return self.chat_repository.create_session(user_id=user_id, detection_id=detection_id)

    async def ask(
        self, user_id: int, session_id: int, question: str, use_web_search: bool = False
    ) -> ChatResponseData:
        session = self.chat_repository.get_session(session_id, user_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró la sesión de chat indicada.",
            )

        plant: str | None = None
        disease: str | None = None
        confidence: float | None = None
        crop_name: str | None = None
        crop_variety: str | None = None

        if session.detection_id is not None:
            detection = self.detection_repository.get_by_id(session.detection_id, user_id)
            if detection is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No se encontró la detección asociada a esta sesión.",
                )
            plant = detection.plant
            disease = detection.disease
            confidence = detection.confidence
            crop_name = detection.crop_name
            crop_variety = detection.crop_variety
        # Si session.detection_id es None, plant/disease/confidence quedan en
        # None a propósito: openai_service arma un prompt "general" distinto.

        history_messages = self.chat_repository.get_messages(session_id)
        history = [{"role": m.role, "content": m.content} for m in history_messages]

        # Guardamos la pregunta del usuario antes de llamar a OpenAI para no perderla
        # si la llamada falla.
        self.chat_repository.add_message(session_id=session_id, role="user", content=question)

        sources: list[dict] | None = None
        try:
            if use_web_search:
                answer, raw_sources = await ask_assistant_with_web_search(
                    plant=plant,
                    disease=disease,
                    confidence=confidence,
                    question=question,
                    history=history,
                    crop_name=crop_name,
                    crop_variety=crop_variety,
                )
                sources = raw_sources or None
            else:
                answer = await ask_assistant(
                    plant=plant,
                    disease=disease,
                    confidence=confidence,
                    question=question,
                    history=history,
                    crop_name=crop_name,
                    crop_variety=crop_variety,
                )
        except OpenAIServiceError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        assistant_message = self.chat_repository.add_message(
            session_id=session_id, role="assistant", content=answer, sources=sources
        )

        return ChatResponseData(
            session_id=session_id,
            answer=answer,
            message_id=assistant_message.id,
            sources=[ChatSourceItem(**s) for s in sources] if sources else None,
        )