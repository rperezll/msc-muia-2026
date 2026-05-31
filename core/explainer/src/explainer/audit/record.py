from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class AuditRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    report_id: str
    source_key: str
    provider: str
    model: str
    temperature: float
    preprocess_ms: int
    llm_ms: int
    total_ms: int
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    tokens_per_second: float | None
    prompt_chars: int
    status: str  # "ok" | "error"
    anomaly_type: str | None = None
    affected_subsystem: str | None = None
    summary: str | None = None
    rag_queries: list[str] | None = None
    error_type: str | None = None
    error_message: str | None = None
