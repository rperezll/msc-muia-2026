from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from shared_lib.schemas.rag import AugmentResponse


class ExplanationFilters(BaseModel):
    source_key: str | None = None
    severity: str | None = None
    anomaly_type: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class ExplanationRecord(BaseModel):
    id: str
    source_key: str
    result: Any
    report: Any | None = None
    duration_ms: int | None = None
    feedback: str | None = None
    feedback_at: datetime | None = None
    created_at: datetime | None = None
    augmented_result: AugmentResponse | None = None


class ExplanationListResponse(BaseModel):
    items: list[ExplanationRecord]
    total: int
    limit: int
    offset: int


class FeedbackRequest(BaseModel):
    feedback: str | None = Field(default=None, pattern="^(up|down)$")
