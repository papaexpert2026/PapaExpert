"""
Validación de archivos de imagen subidos por el usuario.
"""

from fastapi import UploadFile, HTTPException, status

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def validate_image_file(file: UploadFile, max_size_bytes: int, contents: bytes) -> None:
    """
    Lanza HTTPException si el archivo no es una imagen válida o supera el tamaño máximo.

    Se recibe 'contents' ya leído (bytes) para poder validar el tamaño real,
    ya que UploadFile.size no siempre está disponible según el cliente.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Formato de imagen no soportado. Usa JPG, JPEG o PNG.",
        )

    filename = (file.filename or "").lower()
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Extensión de archivo no soportada. Usa .jpg, .jpeg o .png.",
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El archivo de imagen está vacío.",
        )

    if len(contents) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"La imagen supera el tamaño máximo permitido ({max_size_bytes // (1024 * 1024)} MB).",
        )
