"""
Rutas de verificación de estado del backend.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    """
    GET /api/v1/health

    Verifica que el backend está activo y que la conexión a
    PostgreSQL funciona correctamente.

    Response 200:
    {
        "success": true,
        "data": { "database": "connected" },
        "message": "PapaExpert backend operativo."
    }
    """
    try:
        db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        database_status = "disconnected"

    return {
        "success": True,
        "data": {"database": database_status},
        "message": "PapaExpert backend operativo.",
    }
