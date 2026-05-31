from typing import Any

from pydantic import BaseModel


class ExplanationRecord(BaseModel):
    id: str
    source_key: str
    result: Any
    duration_ms: int | None = None
