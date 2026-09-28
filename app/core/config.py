"""
Configuración central del backend PapaExpert.

Todas las variables de entorno se leen y validan exclusivamente aquí.
Ningún otro módulo debe usar os.environ / os.getenv directamente.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === App ===
    APP_NAME: str = "PapaExpert"
    APP_ENV: str = "development"

    # === Base de datos ===
    DATABASE_URL: str

    # === OpenAI ===
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4.1-mini"

    # === YOLO ===
    YOLO_MODEL_PATH: str = "models/best.pt"
    YOLO_CONFIDENCE: float = 0.5

    # === CORS ===
    CORS_ORIGINS: str = "http://localhost"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # === Autenticación ===
    JWT_SECRET: str = "change-me-in-env"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # === Uploads ===
    MAX_UPLOAD_SIZE_MB: int = 8
    UPLOAD_DIR: str = "uploads"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """
    Retorna una instancia única (cacheada) de Settings.
    Se usa como dependencia de FastAPI o como import directo.
    """
    return Settings()


settings = get_settings()
