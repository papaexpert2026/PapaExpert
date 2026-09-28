"""
Acceso a datos de la caché de investigaciones web (tabla research_cache).
"""

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.research_cache_model import ResearchCache

# Después de este tiempo, una investigación cacheada se considera vieja
# y se vuelve a buscar en internet (la información médica/agrícola cambia).
CACHE_TTL_DAYS = 30


class ResearchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_fresh(self, disease: str) -> ResearchCache | None:
        stmt = select(ResearchCache).where(ResearchCache.disease == disease)
        cached = self.db.execute(stmt).scalar_one_or_none()
        if cached is None:
            return None

        updated_at = cached.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) - updated_at > timedelta(days=CACHE_TTL_DAYS):
            return None
        return cached

    def upsert(self, disease: str, content: str, sources: list[dict]) -> ResearchCache:
        stmt = select(ResearchCache).where(ResearchCache.disease == disease)
        existing = self.db.execute(stmt).scalar_one_or_none()

        if existing is not None:
            existing.content = content
            existing.sources_json = json.dumps(sources)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        record = ResearchCache(disease=disease, content=content, sources_json=json.dumps(sources))
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
