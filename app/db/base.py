"""
Clase base declarativa de SQLAlchemy.

Todos los modelos (User, Detection, ChatSession, ChatMessage) heredan de Base.
Alembic usa Base.metadata para autogenerar migraciones.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
