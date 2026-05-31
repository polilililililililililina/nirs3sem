from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgeSource(str, Enum):
    manual = "manual"
    external = "external"


class KnowledgeArticle(BaseModel):
    id: str = Field(alias="_id")
    title: str
    body: str
    tags: list[str] = []
    pathology_type: Optional[str] = None
    source: KnowledgeSource = KnowledgeSource.manual
    source_url: Optional[str] = None
    is_external: bool = False
    author_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True
    }


class KnowledgeArticleCreate(BaseModel):
    title: str
    body: str
    tags: list[str] = []
    pathology_type: Optional[str] = None


class KnowledgeArticleUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[list[str]] = None
    pathology_type: Optional[str] = None


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeArticle]
    pagination: Pagination
