from pydantic import BaseModel


class RagDocument(BaseModel):
    title: str | None = None
    source: str | None = None
    snippet: str
    score: float | None = None


class AugmentResponse(BaseModel):
    augmented_summary: str
    retrieved: list[RagDocument]
    model: str
