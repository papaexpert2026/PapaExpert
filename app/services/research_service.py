"""
Orquesta la investigación web de una enfermedad: revisa la caché primero,
y solo llama a OpenAI (con la herramienta web_search) si no hay nada
reciente guardado.
"""

import json

from app.repositories.research_repository import ResearchRepository
from app.schemas.research_schema import ResearchResponseData, ResearchSourceItem
from app.services.openai_service import research_disease


class ResearchService:
    def __init__(self, db) -> None:
        self.repository = ResearchRepository(db)

    async def get_research(self, plant: str, disease: str) -> ResearchResponseData:
        cached = self.repository.get_fresh(disease)
        if cached is not None:
            return ResearchResponseData(
                disease=disease,
                content=cached.content,
                sources=[ResearchSourceItem(**s) for s in json.loads(cached.sources_json)],
                from_cache=True,
            )

        content, sources = await research_disease(plant=plant, disease=disease)
        self.repository.upsert(disease=disease, content=content, sources=sources)

        return ResearchResponseData(
            disease=disease,
            content=content,
            sources=[ResearchSourceItem(**s) for s in sources],
            from_cache=False,
        )
