"""
POST /api/v1/predictions

Sube una imagen, ejecuta YOLO y guarda la detección resultante.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_firebase_uid
from app.core.config import settings
from app.db.session import get_db
from app.models.user_model import User
from app.repositories.crop_repository import CropRepository
from app.services.prediction_service import PredictionService
from app.services.transient_prediction_service import TransientPredictionService
from app.utils.file_validator import validate_image_file
from app.utils.response_builder import success_response

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("")
async def create_prediction(
    file: UploadFile = File(...),
    crop_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Headers: Authorization: Bearer <token>
    Request: multipart/form-data con el campo 'file' (imagen JPG/JPEG/PNG)
             y opcionalmente 'crop_id' (entero) para asociar el diagnóstico
             a un cultivo ya registrado.

    Response 200:
    {
      "success": true,
      "data": {
        "detection_id": 12,
        "plant": "papa",
        "detections": [ { "class_id":..., "class_name":..., "display_name":...,
                           "confidence":..., "bbox": {...}, "description":..., "recommendation":... } ],
        "image_url": "uploads/xxx.jpg",
        "crop_id": 3,
        "crop_name": "Parcela San José",
        "crop_variety": "Superchola"
      },
      "message": "..."
    }

    Errores posibles:
    - 401 si no hay token válido
    - 404 si se envía un crop_id que no existe o no pertenece al usuario
    - 413 si la imagen supera el tamaño máximo
    - 422 si el formato de archivo no es válido
    - 500 si YOLO falla al procesar la imagen
    - 503 si el modelo YOLO no está disponible (best.pt no encontrado)
    """
    if crop_id is not None:
        crop = CropRepository(db).get_by_id(crop_id, current_user.id)
        if crop is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El cultivo indicado no existe o no te pertenece.",
            )

    contents = await file.read()
    validate_image_file(file, settings.max_upload_size_bytes, contents)

    service = PredictionService(db)
    result = service.run_prediction(
        user_id=current_user.id,
        contents=contents,
        original_filename=file.filename or "image.jpg",
        crop_id=crop_id,
    )

    if not result.detections:
        return success_response(
            data=result.model_dump(),
            message="No se detectó una enfermedad con suficiente confianza.",
        )

    return success_response(data=result.model_dump(), message="Análisis completado.")



@router.post("/process")
async def process_prediction_with_firebase(
    file: UploadFile = File(...),
    _firebase_uid: str = Depends(get_firebase_uid),
) -> dict:
    """Analiza para la app; la persistencia queda en Firebase."""
    contents = await file.read()
    validate_image_file(file, settings.max_upload_size_bytes, contents)
    result = TransientPredictionService().run(
        contents=contents,
        original_filename=file.filename or "image.jpg",
    )
    message = (
        "Análisis completado."
        if result.detections
        else "No se detectó una enfermedad con suficiente confianza."
    )
    return success_response(data=result.model_dump(), message=message)
