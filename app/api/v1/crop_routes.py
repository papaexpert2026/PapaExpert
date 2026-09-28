"""
POST   /api/v1/crops
GET    /api/v1/crops
GET    /api/v1/crops/{id}
PUT    /api/v1/crops/{id}
DELETE /api/v1/crops/{id}
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user_model import User
from app.repositories.crop_repository import CropRepository
from app.schemas.crop_schema import CropCreateRequest, CropListResponse, CropOut
from app.utils.response_builder import success_response

router = APIRouter(prefix="/crops", tags=["Crops"])


@router.post("")
def create_crop(
    payload: CropCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Headers: Authorization: Bearer <token>
    Request: { "name", "variety", "planting_date" (YYYY-MM-DD), "area_hectares"?,
               "location_label"?, "latitude"?, "longitude"?, "notes"? }
    Response 200: el cultivo creado.
    """
    repository = CropRepository(db)
    crop = repository.create(user_id=current_user.id, data=payload)
    return success_response(data=CropOut.model_validate(crop).model_dump(), message="Cultivo registrado.")


@router.get("")
def list_crops(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Response 200: lista de cultivos del usuario, más recientes primero."""
    repository = CropRepository(db)
    items, total = repository.list_by_user(current_user.id, limit=limit, offset=offset)
    payload = CropListResponse(items=[CropOut.model_validate(c) for c in items], total=total)
    return success_response(data=payload.model_dump(), message="Cultivos obtenidos.")


@router.get("/{crop_id}")
def get_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Response 200: detalle de un cultivo. Errores: 404 si no existe o no es tuyo."""
    repository = CropRepository(db)
    crop = repository.get_by_id(crop_id, current_user.id)
    if crop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivo no encontrado.")
    return success_response(data=CropOut.model_validate(crop).model_dump(), message="Cultivo obtenido.")


@router.put("/{crop_id}")
def update_crop(
    crop_id: int,
    payload: CropCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Actualiza todos los campos del cultivo (reemplazo completo). Errores: 404."""
    repository = CropRepository(db)
    crop = repository.get_by_id(crop_id, current_user.id)
    if crop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivo no encontrado.")
    updated = repository.update(crop, payload)
    return success_response(data=CropOut.model_validate(updated).model_dump(), message="Cultivo actualizado.")


@router.delete("/{crop_id}")
def delete_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Elimina un cultivo. Errores: 404 si no existe o no es tuyo."""
    repository = CropRepository(db)
    crop = repository.get_by_id(crop_id, current_user.id)
    if crop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivo no encontrado.")
    repository.delete(crop)
    return success_response(data=None, message="Cultivo eliminado.")
