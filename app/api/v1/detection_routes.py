"""
GET /api/v1/detections
GET /api/v1/detections/{id}
GET /api/v1/detections/{id}/research
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user_model import User
from app.repositories.detection_repository import DetectionRepository
from app.schemas.detection_schema import DetectionListResponse, DetectionOut
from app.services.openai_service import OpenAIServiceError
from app.services.research_service import ResearchService
from app.utils.response_builder import success_response

router = APIRouter(prefix="/detections", tags=["Detections"])


@router.get("")
def list_detections(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Headers: Authorization: Bearer <token>
    Query params: limit (1-100, default 20), offset (default 0)

    Response 200: lista de detecciones del usuario ordenadas por fecha descendente.
    """
    repository = DetectionRepository(db)
    items, total = repository.list_by_user(current_user.id, limit=limit, offset=offset)

    payload = DetectionListResponse(
        items=[DetectionOut.model_validate(item) for item in items],
        total=total,
    )
    return success_response(data=payload.model_dump(), message="Detecciones obtenidas.")


@router.get("/{detection_id}")
def get_detection(
    detection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Headers: Authorization: Bearer <token>

    Response 200: detalle de una detección.
    Errores: 404 si la detección no existe o no pertenece al usuario.
    """
    repository = DetectionRepository(db)
    detection = repository.get_by_id(detection_id, current_user.id)
    if detection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detección no encontrada.")

    return success_response(
        data=DetectionOut.model_validate(detection).model_dump(),
        message="Detección obtenida.",
    )


@router.get("/{detection_id}/research")
async def get_detection_research(
    detection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Headers: Authorization: Bearer <token>

    Busca en internet (con caché de hasta 30 días por enfermedad) artículos
    e información actualizada sobre la enfermedad de esta detección, para
    mostrar ANTES de que el usuario entre al chat.

    Response 200: { "disease":..., "content":..., "sources":[{"title","url"}], "from_cache": bool }
    Errores: 404 si la detección no existe, 503 si la búsqueda web falla.
    """
    repository = DetectionRepository(db)
    detection = repository.get_by_id(detection_id, current_user.id)
    if detection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detección no encontrada.")

    service = ResearchService(db)
    try:
        result = await service.get_research(plant=detection.plant, disease=detection.disease)
    except OpenAIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return success_response(data=result.model_dump(), message="Investigación obtenida.")
