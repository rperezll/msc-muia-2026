from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExplanationRecord(BaseModel):
    id: str
    source_key: str
    result: Any
    report: Any | None = None
    duration_ms: int | None = None
    feedback: str | None = None
    feedback_at: datetime | None = None
    created_at: datetime | None = None


class ExplanationListResponse(BaseModel):
    items: list[ExplanationRecord]
    total: int
    limit: int
    offset: int


class FeedbackRequest(BaseModel):
    feedback: str | None = Field(default=None, pattern="^(up|down)$")
