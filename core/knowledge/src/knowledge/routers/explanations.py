from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from knowledge.dependencies import get_explanation_repo, get_rag_service
from knowledge.rag.service import RagService
from shared_lib.config import config
from shared_lib.db.repositories.explanation import ExplanationFilters, ExplanationRepository
from shared_lib.schemas import (
    AugmentResponse,
    ExplanationListResponse,
    ExplanationRecord,
    FeedbackRequest,
)

router = APIRouter(prefix="/api/explanations", tags=["explanations"])

RepoDep = Annotated[ExplanationRepository, Depends(get_explanation_repo)]
RagDep = Annotated[RagService, Depends(get_rag_service)]


@router.get("", response_model=ExplanationListResponse)
def list_explanations(
    repo: RepoDep,
    source_key: str | None = None,
    severity: str | None = None,
    anomaly_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ExplanationListResponse:
    cfg = config.knowledge
    effective_limit = min(limit or cfg.default_page_size, cfg.max_page_size)
    filters = ExplanationFilters(
        source_key=source_key,
        severity=severity,
        anomaly_type=anomaly_type,
        date_from=date_from,
        date_to=date_to,
    )
    items = repo.list(filters=filters, limit=effective_limit, offset=offset)
    total = repo.count(filters=filters)
    return ExplanationListResponse(items=items, total=total, limit=effective_limit, offset=offset)


@router.get("/{explanation_id}", response_model=ExplanationRecord)
def get_explanation(explanation_id: str, repo: RepoDep) -> ExplanationRecord:
    record = repo.get(explanation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Explanation not found")
    return record


@router.patch("/{explanation_id}/feedback", response_model=ExplanationRecord)
def set_feedback(explanation_id: str, body: FeedbackRequest, repo: RepoDep) -> ExplanationRecord:
    record = repo.set_feedback(explanation_id, body.feedback)
    if not record:
        raise HTTPException(status_code=404, detail="Explanation not found")
    return record


@router.post("/{explanation_id}/augment", response_model=AugmentResponse)
def augment_explanation(explanation_id: str, repo: RepoDep, rag: RagDep) -> AugmentResponse:
    record = repo.get(explanation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Explanation not found")

    try:
        incidents = record.result if isinstance(record.result, list) else []
        first = incidents[0] if incidents else {}
        summary = first.get("technical_description", {}).get("summary", "")
        rag_queries = first.get("suggested_rag_search_queries", [])
    except (IndexError, AttributeError, TypeError):
        raise HTTPException(status_code=422, detail="Malformed explanation result") from None

    if not rag_queries:
        raise HTTPException(status_code=422, detail="Explanation has no RAG queries")

    return rag.augment(summary=summary, rag_queries=rag_queries)
