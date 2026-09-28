"""
Configuración del engine de SQLAlchemy y la fábrica de sesiones.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


database_url = settings.DATABASE_URL

if database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )


engine = create_engine(
    database_url,
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
