from typing import Literal, Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class Citation(BaseModel):
    section_id: str
    title: str
    source_file: str
    text: str
    score: float


class AskResponse(BaseModel):
    type: Literal["answered", "not_covered", "conflict"]
    answer: str
    citations: list[Citation]
    confidence: Optional[Literal["high", "medium", "low"]] = None
