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

from app.core.config import settings

# Los paths relativos se anclan al directorio del backend; los absolutos
# permiten usar un disco persistente de Render (por ejemplo /var/data/uploads).
BASE_DIR = Path(__file__).resolve().parent.parent.parent
configured_upload_dir = Path(settings.UPLOAD_DIR)
UPLOADS_DIR = (
    configured_upload_dir
    if configured_upload_dir.is_absolute()
    else BASE_DIR / configured_upload_dir
)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
