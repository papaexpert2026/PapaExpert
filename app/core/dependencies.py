"""
Dependencias comunes de FastAPI: usuario autenticado actual.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from pathlib import Path
import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials as firebase_credentials

from app.core.config import settings
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user_model import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación. Incluye el header Authorization: Bearer <token>.",
        )

    email = decode_access_token(credentials.credentials)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado. Inicia sesión nuevamente.",
        )

    user = UserRepository(db).get_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado.",
        )

    return user


_firebase_logger = logging.getLogger(__name__)


def get_firebase_uid(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Valida el ID token de Firebase sin crear usuarios ni acceder a SQL."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación Firebase.",
        )

    service_account_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH
    if settings.APP_ENV == "production" and (
        not service_account_path or not Path(service_account_path).is_file()
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configura el archivo de credenciales Firebase Admin en Render.",
        )

    try:
        if not firebase_admin._apps:
            service_account = (
                firebase_credentials.Certificate(service_account_path)
                if service_account_path else None
            )
            firebase_admin.initialize_app(
                credential=service_account,
                options={"projectId": settings.FIREBASE_PROJECT_ID},
            )
    except Exception as exc:
        _firebase_logger.exception("Firebase Admin no pudo inicializarse.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servidor no tiene credenciales de Firebase Admin configuradas.",
        ) from exc

    try:
        claims = firebase_auth.verify_id_token(credentials.credentials, clock_skew_seconds=60)
        return str(claims["uid"])
    except Exception as exc:
        _firebase_logger.warning(
            "Firebase rechazó el ID token (%s): %s", type(exc).__name__, exc
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Firebase inválido o expirado.",
        ) from exc
