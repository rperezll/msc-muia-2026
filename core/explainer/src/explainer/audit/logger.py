from pathlib import Path

from shared_lib.logger import get_logger

from .record import AuditRecord

log = get_logger("explainer.audit")


class AuditLogger:
    def __init__(self, path: str = "logs/audit.jsonl") -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: AuditRecord) -> None:
        try:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(record.model_dump_json() + "\n")
        except Exception as e:
            log.error("Error escribiendo audit: %s", e)
