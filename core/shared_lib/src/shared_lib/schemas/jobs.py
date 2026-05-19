from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from shared_lib.schemas.anomaly import AnomalyReport


class JobEventType(StrEnum):
    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"


class JobEvent(BaseModel):
    """Evento de ciclo de vida de un job de explicación, publicado en RabbitMQ y MQTT"""

    type: JobEventType
    report_id: str
    source_key: str
    started_at: datetime | None = None
    iteration: int | None = None
    max_iterations: int | None = None
    result: Any | None = None
    duration_ms: int | None = None
    error: str | None = None
    report: AnomalyReport | None = None
