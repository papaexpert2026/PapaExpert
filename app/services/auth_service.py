"""
Lógica de negocio de autenticación: registro, login y login con Firebase.
"""

import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.firebase import verify_firebase_token
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.repository = UserRepository(db)

    def register(self, email: str, password: str) -> str:
        existing = self.repository.get_by_email(email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cuenta registrada con ese correo.",
            )
        user = self.repository.create(email=email, hashed_password=hash_password(password))
        return create_access_token(subject=user.email)

    def login(self, email: str, password: str) -> str:
        user = self.repository.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(

                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos.",
            )
        return create_access_token(subject=user.email)

    def login_with_firebase(self, id_token: str) -> str:
        try:
            decoded = verify_firebase_token(id_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de Firebase inválido o expirado.",
            )

        email = decoded.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta de Firebase no tiene correo.",
            )

        user = self.repository.get_by_email(email)
        if user is None:
            user = self.repository.create(
                email=email,
                hashed_password=hash_password(secrets.token_urlsafe(32)),
            )
        return create_access_token(subject=user.email)