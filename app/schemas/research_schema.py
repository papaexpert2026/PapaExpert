"""
Esquemas Pydantic para el endpoint de investigación web de una enfermedad.
"""

from pydantic import BaseModel


class ResearchSourceItem(BaseModel):
    title: str
    url: str


class ResearchResponseData(BaseModel):
    disease: str
    content: str
    sources: list[ResearchSourceItem]
    from_cache: bool
