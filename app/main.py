"""
Punto de entrada de PapaExpert backend.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
from pathlib import Path

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.paths import UPLOADS_DIR  # <-- CAMBIO: misma fuente que prediction_service.py


# ============================================================
# APLICACIÓN FASTAPI
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API para detección de enfermedades en plantas de papa "
        "mediante YOLO, con asistente conversacional basado en OpenAI."
    ),
    version="1.0.0",
)

_logger = logging.getLogger(__name__)
_treatment_notification_task: asyncio.Task | None = None


async def _run_treatment_notification_worker() -> None:
    from app.services.treatment_notification_service import (
        process_due_treatment_notifications,
    )

    while True:
        try:
            count = await asyncio.to_thread(process_due_treatment_notifications)
            if count:
                _logger.info("Se enviaron %s notificaciones de tratamiento.", count)
        except asyncio.CancelledError:
            raise
        except Exception:
            _logger.exception("Falló el ciclo de notificaciones de tratamientos.")
        await asyncio.sleep(30)


@app.on_event("startup")
async def start_treatment_notification_worker() -> None:
    global _treatment_notification_task
    service_account_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH
    if service_account_path and not Path(service_account_path).is_file():
        _logger.error(
            "No se inicia el worker de tratamientos: no existe el archivo de "
            "credenciales Firebase configurado en FIREBASE_SERVICE_ACCOUNT_PATH."
        )
        return
    if not service_account_path and settings.APP_ENV == "production":
        _logger.error(
            "No se inicia el worker de tratamientos: configura el archivo "
            "de credenciales de Firebase Admin en Render."
        )
        return

    _treatment_notification_task = asyncio.create_task(
        _run_treatment_notification_worker()
    )


@app.on_event("shutdown")
async def stop_treatment_notification_worker() -> None:
    if _treatment_notification_task is not None:
        _treatment_notification_task.cancel()
        try:
            await _treatment_notification_task
        except asyncio.CancelledError:
            pass


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ARCHIVOS ESTÁTICOS
# ============================================================

# Permite acceder desde Flutter a las imágenes guardadas
# físicamente dentro de UPLOADS_DIR (ver app/core/paths.py).
#
# Ejemplo:
#
# http://192.168.1.6:8000/uploads/9934937d61fb48828292635299ecb905.jpg
#
# FastAPI buscará físicamente en UPLOADS_DIR / "9934937d...jpg"
#
# IMPORTANTE: prediction_service.py usa esta MISMA UPLOADS_DIR (importada
# desde app.core.paths) para guardar los archivos. Ya no pueden
# desincronizarse, sin importar desde qué carpeta ejecutes uvicorn.

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOADS_DIR)),
    name="uploads",
)


# ============================================================
# RUTAS DE LA API
# ============================================================

app.include_router(api_router)


# ============================================================
# MENSAJES DE VALIDACIÓN
# ============================================================

_VALIDATION_MESSAGES = {
    "value_error": "El valor ingresado no es válido.",
    "missing": "Falta un campo obligatorio.",
    "string_too_short": "El valor ingresado es demasiado corto.",
    "string_too_long": "El valor ingresado es demasiado largo.",
    "int_parsing": "Se esperaba un número entero.",
    "float_parsing": "Se esperaba un número.",
}


# ============================================================
# MANEJADOR DE ERRORES DE VALIDACIÓN
# ============================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Convierte los errores de validación de Pydantic/FastAPI
    al formato JSON consistente que usa el resto de la API.
    """

    first_error = exc.errors()[0] if exc.errors() else None

    field = (
        first_error["loc"][-1]
        if first_error and first_error.get("loc")
        else None
    )

    error_type = (
        first_error.get("type", "")
        if first_error
        else ""
    )

    base_message = _VALIDATION_MESSAGES.get(
        error_type,
        "Los datos enviados no son válidos.",
    )

    message = (
        f"{base_message} (campo: {field})"
        if field
        else base_message
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
             "message": message,
            "error_code": "VALIDATION_ERROR",
        },
    )


# ============================================================
# RUTA PRINCIPAL
# ============================================================

@app.get("/", tags=["Root"])
def root() -> dict:
    return {
        "success": True,
        "data": {
            "app": settings.APP_NAME,
            "docs": "/docs",
            "uploads": "/uploads/",
        },
        "message": "Bienvenido a la API de PapaExpert.",
    }
