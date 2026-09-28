"""
Ruta única y absoluta de la carpeta de uploads.

Este archivo existe para que NINGÚN otro módulo tenga que calcular por su
cuenta dónde está la carpeta de imágenes. Antes, main.py y
prediction_service.py calculaban la ruta cada uno por su lado (uno con
BASE_DIR, el otro con settings.UPLOAD_DIR relativo) y podían apuntar a
carpetas distintas según desde dónde se ejecutara uvicorn.

Ahora: TODOS importan UPLOADS_DIR desde aquí. Un solo lugar, un solo valor,
sin importar el directorio de trabajo actual (cwd) al iniciar el servidor.
"""

from pathlib import Path

# Este archivo está en: backend/app/core/paths.py
# parent       -> backend/app/core
# parent.parent -> backend/app
# parent.parent.parent -> backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent

UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)