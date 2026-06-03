from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from psycopg.types.json import Jsonb

from shared_lib.logger import get_logger
from shared_lib.schemas.explanation import ExplanationFilters, ExplanationRecord

if TYPE_CHECKING:
    from shared_lib.db.postgres import PostgresTransport
    from shared_lib.schemas.jobs import JobEvent

log = get_logger("postgres")

_INSERT = """
    INSERT INTO explanations (id, source_key, result, report, duration_ms)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (id) DO NOTHING
"""

_SELECT_BASE = """
    SELECT id, source_key, result, report, duration_ms, feedback, feedback_at, created_at
    FROM explanations
"""


def _row_to_record(row: tuple) -> ExplanationRecord:
    id_, source_key, result, report, duration_ms, feedback, feedback_at, created_at = row
    return ExplanationRecord(
        id=id_,
        source_key=source_key,
        result=result,
        report=report,
        duration_ms=duration_ms,
        feedback=feedback,
        feedback_at=feedback_at,
        created_at=created_at,
    )


def _build_where(filters: ExplanationFilters) -> tuple[str, list[Any]]:
    """Construye cláusula WHERE y lista de params para los filtros dados"""
    clauses: list[str] = []
    params: list[Any] = []

    if filters.source_key:
        clauses.append("source_key = %s")
        params.append(filters.source_key)
    if filters.severity:
        clauses.append("result #>> '{0,event_metadata,severity}' = %s")
        params.append(filters.severity)
    if filters.anomaly_type:
        clauses.append("result #>> '{0,rag_search_parameters,anomaly_type}' = %s")
        params.append(filters.anomaly_type)
    if filters.date_from:
        clauses.append("created_at >= %s")
        params.append(filters.date_from)
    if filters.date_to:
        clauses.append("created_at <= %s")
        params.append(filters.date_to)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


class ExplanationRepository:
    """Persiste y consulta explicaciones del módulo Explainer"""

    def __init__(self, transport: PostgresTransport) -> None:
        self._transport = transport

    def save(self, event: JobEvent) -> None:
        result = json.loads(event.result) if isinstance(event.result, str) else event.result
        report = event.report.model_dump(mode="json") if event.report else None
        with self._transport.cursor() as cur:
            cur.execute(
                _INSERT,
                (
                    event.report_id,
                    event.source_key,
                    Jsonb(result),
                    Jsonb(report) if report else None,
                    event.duration_ms,
                ),
            )

    def get(self, explanation_id: str) -> ExplanationRecord | None:
        with self._transport.cursor() as cur:
            cur.execute(_SELECT_BASE + "WHERE id = %s", (explanation_id,))
            row = cur.fetchone()
        return _row_to_record(row) if row else None

    def list(
        self,
        filters: ExplanationFilters | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ExplanationRecord]:
        f = filters or ExplanationFilters()
        where, params = _build_where(f)
        query = f"{_SELECT_BASE} {where} ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
        params += [limit, offset]
        with self._transport.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        return [_row_to_record(r) for r in rows]

    def count(self, filters: ExplanationFilters | None = None) -> int:
        f = filters or ExplanationFilters()
        where, params = _build_where(f)
        query = f"SELECT COUNT(*) FROM explanations {where}"
        with self._transport.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
        return row[0] if row else 0

    def set_feedback(self, explanation_id: str, feedback: str | None) -> ExplanationRecord | None:
        sql = """
            UPDATE explanations
            SET feedback = %s, feedback_at = CASE WHEN %s IS NULL THEN NULL ELSE now() END
            WHERE id = %s
        """
        with self._transport.cursor() as cur:
            cur.execute(sql, (feedback, feedback, explanation_id))
        return self.get(explanation_id)
