from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from knowledge.app import create_app
from knowledge.dependencies import get_explanation_repo, get_rag_service
from knowledge.schemas import AugmentResponse
from shared_lib.schemas.explanation import ExplanationRecord

if TYPE_CHECKING:
    from shared_lib.schemas.explanation import ExplanationFilters

_NOW = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)

SAMPLE_RESULT = [
    {
        "event_metadata": {
            "timestamp": "2025-01-01T12:00:00",
            "severity": "HIGH",
            "instance_id": "inv-1",
        },
        "rag_search_parameters": {
            "generic_component_class": "Solar Inverter",
            "anomaly_type": "power_degradation",
            "affected_subsystem": "DC/AC Conversion",
        },
        "technical_description": {
            "original_metrics": {"mae": 0.5, "threshold": 0.3},
            "summary": "Test summary.",
        },
        "suggested_rag_search_queries": ["query 1", "query 2", "query 3"],
    }
]

SAMPLE_RECORD = ExplanationRecord(
    id="test-id-1",
    source_key="inv-1",
    result=SAMPLE_RESULT,
    report=None,
    duration_ms=1234,
    feedback=None,
    feedback_at=None,
    created_at=_NOW,
)


class FakeRepo:
    def __init__(self, records: list[ExplanationRecord] | None = None) -> None:
        self._records: dict[str, ExplanationRecord] = {
            r.id: r for r in (records or [SAMPLE_RECORD])
        }

    def get(self, explanation_id: str) -> ExplanationRecord | None:
        return self._records.get(explanation_id)

    def list(
        self,
        filters: ExplanationFilters | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ExplanationRecord]:
        items = list(self._records.values())
        return items[offset : offset + limit]

    def count(self, filters: ExplanationFilters | None = None) -> int:
        return len(self._records)

    def set_feedback(
        self, explanation_id: str, feedback: str | None
    ) -> ExplanationRecord | None:
        r = self._records.get(explanation_id)
        if r is None:
            return None
        updated = r.model_copy(
            update={"feedback": feedback, "feedback_at": _NOW if feedback else None}
        )
        self._records[explanation_id] = updated
        return updated


class FakeRagService:
    def augment(self, summary: str, rag_queries: list[str]) -> AugmentResponse:
        return AugmentResponse(
            augmented_summary="Augmented: " + summary,
            retrieved=[],
            model="gpt-4o-mini",
        )


@pytest.fixture
def fake_repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def client(fake_repo: FakeRepo) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_explanation_repo] = lambda: fake_repo
    app.dependency_overrides[get_rag_service] = lambda: FakeRagService()
    return TestClient(app)
