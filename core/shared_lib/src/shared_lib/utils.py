from datetime import UTC, datetime
from uuid import uuid4

MINUTES_IN_DAY = 1440


def new_id() -> str:
    """Genera un UUID4 como string"""
    return str(uuid4())


def now_utc() -> datetime:
    """Devuelve el instante actual en UTC"""
    return datetime.now(UTC)
