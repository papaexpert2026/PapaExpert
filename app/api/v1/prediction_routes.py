"""
POST /api/v1/predictions

Sube una imagen, ejecuta YOLO y guarda la detección resultante.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user_model import User
from app.services.prediction_service import PredictionService
from app.utils.file_validator import validate_image_file
from app.utils.response_builder import success_response

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("")
async def create_prediction(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Headers: Authorization: Bearer <token>
    Request: multipart/form-data con el campo 'file' (imagen JPG/JPEG/PNG)

    Response 200:
    {
      "success": true,
      "data": {
        "detection_id": 12,
        "plant": "papa",
        "detections": [ { "class_id":..., "class_name":..., "display_name":...,
                           "confidence":..., "bbox": {...}, "description":..., "recommendation":... } ],
        "image_url": "uploads/xxx.jpg"
      },
      "message": "..."
    }

    Errores posibles:
    - 401 si no hay token válido
    - 413 si la imagen supera el tamaño máximo
    - 422 si el formato de archivo no es válido
    - 500 si YOLO falla al procesar la imagen
    - 503 si el modelo YOLO no está disponible (best.pt no encontrado)
    """
    contents = await file.read()
    validate_image_file(file, settings.max_upload_size_bytes, contents)

    service = PredictionService(db)
    result = service.run_prediction(
        user_id=current_user.id,
        contents=contents,
        original_filename=file.filename or "image.jpg",
    )

    if not result.detections:
        return success_response(
            data=result.model_dump(),
            message="No se detectó una enfermedad con suficiente confianza.",
        )

    return success_response(data=result.model_dump(), message="Análisis completado.")
