"""
Configuración del engine de SQLAlchemy y la fábrica de sesiones.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator:
    """
    Dependencia de FastAPI: entrega una sesión de base de datos por request
    y la cierra automáticamente al finalizar, incluso si hay una excepción.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
