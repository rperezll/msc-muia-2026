from __future__ import annotations

import json
from typing import TYPE_CHECKING

from psycopg.types.json import Jsonb

from shared_lib.logger import get_logger

if TYPE_CHECKING:
    from shared_lib.db.postgres import PostgresTransport
    from shared_lib.schemas.jobs import JobEvent

log = get_logger("postgres")

_INSERT = """
    INSERT INTO explanations (id, source_key, result, duration_ms)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (id) DO NOTHING
"""


class ExplanationRepository:
    """Persiste explicaciones del módulo Explainer"""

    def __init__(self, transport: PostgresTransport) -> None:
        self._transport = transport

    def save(self, event: JobEvent) -> None:
        # Debemos deserializar antes de insertar
        result = json.loads(event.result) if isinstance(event.result, str) else event.result
        with self._transport.cursor() as cur:
            cur.execute(
                _INSERT,
                (event.report_id, event.source_key, Jsonb(result), event.duration_ms),
            )
