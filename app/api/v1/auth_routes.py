"""
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user_model import User
from app.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services.auth_service import AuthService
from app.utils.response_builder import success_response

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    """
    Request: { "email": "...", "password": "..." } (password mínimo 8 caracteres)
    Response 200: { "access_token": "...", "token_type": "bearer" }
    Errores: 409 si el correo ya está registrado.
    """
    service = AuthService(db)
    token = service.register(email=payload.email, password=payload.password)
    return success_response(data=TokenResponse(access_token=token).model_dump(), message="Cuenta creada.")


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    """
    Request: { "email": "...", "password": "..." }
    Response 200: { "access_token": "...", "token_type": "bearer" }
    Errores: 401 si las credenciales son incorrectas.
    """
    service = AuthService(db)
    token = service.login(email=payload.email, password=payload.password)
    return success_response(data=TokenResponse(access_token=token).model_dump(), message="Sesión iniciada.")


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)) -> dict:
    """
    Headers: Authorization: Bearer <token>
    Response 200: datos del usuario autenticado.
    """
    return success_response(data=UserOut.model_validate(current_user).model_dump(), message="Usuario actual.")
