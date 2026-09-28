"""
Punto de entrada de PapaExpert backend.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

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
            "data": None,
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