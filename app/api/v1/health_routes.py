"""
Rutas de verificación de estado del backend.
"""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict:
    """
    GET /api/v1/health

    Verifica que el proceso HTTP está activo. Firebase se valida en las
    rutas protegidas para evitar que Render dependa de PostgreSQL.

    Response 200:
    {
        "success": true,
        "data": { "status": "ok" },
        "message": "PapaExpert backend operativo."
    }
    """
    return {
        "success": True,
        "data": {"status": "ok"},
        "message": "PapaExpert backend operativo.",
    }
